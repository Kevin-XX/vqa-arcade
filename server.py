"""VQA Arcade Web Server —— Flask 后端

启动:
    pip install flask flask-cors numpy Pillow
    python server.py
    浏览器打开 http://localhost:5100
"""
from __future__ import annotations
import io, os, sys, json, threading, uuid, time, base64, traceback
from pathlib import Path
from flask import Flask, Response, request, send_from_directory, jsonify, stream_with_context
from flask_cors import CORS

# 确保 vqa 包在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 延迟导入 —— VSFA 可能因缺少 torch 而无法加载
_vqa_available = True
try:
    from vqa.scorer import Scorer
    from vqa.algos import ALGORITHMS
except Exception as e:
    _vqa_available = False
    _vqa_error = str(e)

app = Flask(__name__)
CORS(app)
_WEB_DIR = Path(__file__).parent / "web"
_UPLOAD_DIR = Path(__file__).parent / "uploads"
_UPLOAD_DIR.mkdir(exist_ok=True)

# ── 任务状态存储 ──
_tasks: dict[str, dict] = {}
_lock = threading.Lock()


# ── 首页 ──
@app.route("/")
def index():
    return send_from_directory(str(_WEB_DIR), "index.html")

# ── 静态资源（字体、图等）──
@app.route("/<path:filename>")
def static_files(filename: str):
    # api 开头的留给接口
    if filename.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    fp = _WEB_DIR / filename
    if fp.is_file():
        return send_from_directory(str(_WEB_DIR), filename)
    return jsonify({"error": "Not found"}), 404


@app.route("/api/health")
def health():
    algos = list(ALGORITHMS.keys()) if _vqa_available else []
    return jsonify({
        "status": "ok" if _vqa_available else "degraded",
        "algorithms": algos,
        "error": None if _vqa_available else _vqa_error,
    })


# ── 文件上传 ──
@app.route("/api/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "缺少文件"}), 400
    fid = uuid.uuid4().hex[:12]
    ext = Path(f.filename).suffix.lower() if f.filename else ".png"
    name = f"{fid}{ext}"
    path = _UPLOAD_DIR / name
    f.save(str(path))
    # 若是图片，生成 base64 预览
    preview = None
    if ext in (".png", ".jpg", ".jpeg", ".bmp"):
        preview = _img_to_base64(str(path))
    return jsonify({
        "file_id": fid, "filename": f.filename,
        "ext": ext, "path": str(path), "preview": preview,
    })


# ── 预览 ──
@app.route("/api/preview/<fid>")
def preview(fid: str):
    # 查找匹配文件
    for f in _UPLOAD_DIR.glob(f"{fid}.*"):
        path = str(f)
        ext = f.suffix.lower()
        if ext in (".mp4", ".mov", ".avi", ".mkv"):
            # 视频：提取首帧
            b64 = _video_first_frame(path)
            return jsonify({"type": "video", "preview": b64})
        b64 = _img_to_base64(path)
        return jsonify({"type": "image", "preview": b64})
    return jsonify({"error": "未找到文件"}), 404


# ── 开始评分 ──
@app.route("/api/score", methods=["POST"])
def score():
    if not _vqa_available:
        return jsonify({"error": f"算法模块不可用: {_vqa_error}"}), 503

    data = request.get_json()
    tid = data.get("task_id") or uuid.uuid4().hex[:12]
    algo = data.get("algo", "PSNR")
    kind = data.get("kind", "FR")
    stride = int(data.get("stride", 1))
    max_frames = data.get("max_frames")
    if max_frames is not None:
        max_frames = int(max_frames) if max_frames > 0 else None

    target_fid = data.get("target")    # file_id
    ref_fid = data.get("reference")   # file_id (FR only)

    t_path = _find_upload(target_fid)
    if not t_path:
        return jsonify({"error": f"未找到目标文件: {target_fid}"}), 404

    r_path = _find_upload(ref_fid) if kind == "FR" else None
    if kind == "FR" and not r_path:
        return jsonify({"error": f"未找到参考文件: {ref_fid}"}), 404

    # 视频帧数预检：无限制时自动设上限，避免长时间无响应
    frame_hint = 0
    if _is_video(t_path):
        frame_hint = _count_video_frames(t_path)
        if max_frames is None or max_frames == 0:
            max_frames = 60  # 默认上限 60 帧
        elif max_frames > 200:
            max_frames = 200  # 最多 200 帧

    with _lock:
        _tasks[tid] = {"status": "pending", "progress": 0.0, "result": None, "error": None}

    t = threading.Thread(target=_run_scoring,
                         args=(tid, algo, t_path, r_path, stride, max_frames), daemon=True)
    t.start()
    return jsonify({"task_id": tid, "frame_hint": frame_hint})


# ── SSE 进度流 ──
@app.route("/api/score/stream/<tid>")
def score_stream(tid: str):
    def _gen():
        last_status = None
        last_heartbeat = time.time()
        for _ in range(600):  # 最多等 10 分钟
            with _lock:
                task = _tasks.get(tid)
            if not task:
                yield f"data: {json.dumps({'error': '任务不存在'})}\n\n"
                return
            status = task["status"]
            upd = json.dumps({
                "status": status, "progress": task["progress"],
                "result": task.get("result"), "error": task.get("error"),
            })
            # 状态变化时发送
            if status != last_status:
                yield f"data: {upd}\n\n"
                last_status = status
            # 运行中每 3 秒发心跳，防止前端认为卡死
            elif status == "running" and time.time() - last_heartbeat > 3:
                yield f"data: {upd}\n\n"
                last_heartbeat = time.time()
            if status in ("done", "error"):
                return
            time.sleep(0.5)
    return Response(stream_with_context(_gen()), mimetype="text/event-stream")


# ── 内部辅助 ──

def _find_upload(fid: str | None) -> str | None:
    if not fid:
        return None
    files = list(_UPLOAD_DIR.glob(f"{fid}.*"))
    return str(files[0]) if files else None


def _img_to_base64(path: str) -> str:
    try:
        from PIL import Image
        img = Image.open(path)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def _video_first_frame(path: str) -> str:
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        ok, frame = cap.read()
        cap.release()
        if ok:
            from PIL import Image
            import numpy as np
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            buf = io.BytesIO()
            img.save(buf, "PNG")
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        pass
    return ""


def _is_video(path: str) -> bool:
    return Path(path).suffix.lower() in (".mp4", ".mov", ".avi", ".mkv", ".webm")

def _count_video_frames(path: str) -> int:
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return count
    except Exception:
        return 0

def _run_scoring(tid: str, algo: str, t_path: str, r_path: str | None,
                 stride: int = 1, max_frames: int | None = None):
    try:
        t0 = time.time()
        with _lock:
            _tasks[tid] = {"status": "running", "progress": 0.02, "result": None, "error": None}

        scorer = Scorer(algo)

        # 真实逐帧进度回调
        def _on_progress(current: int, total: int):
            with _lock:
                if tid in _tasks:
                    _tasks[tid]["progress"] = 0.05 + 0.9 * (current / max(total, 1))

        result = scorer.score(t_path, reference=r_path, stride=stride,
                              max_frames=max_frames or None,
                              progress_callback=_on_progress)
        result["elapsed_sec"] = round(time.time() - t0, 2)
        result.pop("target", None)
        result.pop("reference", None)

        with _lock:
            _tasks[tid] = {"status": "done", "progress": 1.0, "result": result, "error": None}
    except Exception as e:
        with _lock:
            _tasks[tid] = {"status": "error", "progress": 0.0, "result": None,
                           "error": f"{e}\n{traceback.format_exc()}"}
            _tasks[tid] = {"status": "error", "progress": 0.0, "result": None,
                           "error": f"{e}\n{traceback.format_exc()}"}


if __name__ == "__main__":
    print("⚡ VQA ARCADE WEB SERVER")
    print(f"  算法: {list(ALGORITHMS.keys()) if _vqa_available else '不可用'}")
    print("  打开: http://localhost:5100")
    app.run(host="0.0.0.0", port=5100, debug=False, threaded=True)
