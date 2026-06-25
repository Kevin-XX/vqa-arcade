"""GUI 自动演练 + 录制成 GIF。

流程：
  1. 启动 MainWindow（默认 onscreen，可改 offscreen）
  2. 第 1 帧：空白启动
  3. 自动设置参考文件 ref.png 和待评估 dis_blur.png
  4. 第 2 帧：双图加载完成
  5. 选择 SSIM；点击"开始评估"
  6. 异步等待评分完成，期间每 ~150ms 截一帧
  7. 第 N 帧：评分完成，分数和曲线可见
  8. 用 Pillow 合成 reports/gui_demo.gif（限 ≤ 800px 宽，灰度+减色压缩）
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# 切到项目根
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from PIL import Image  # noqa: E402
from PyQt5 import QtCore, QtGui, QtWidgets  # noqa: E402

from vqa.gui.main_window import MainWindow, _STYLE  # noqa: E402

OUT_DIR = ROOT / "reports" / "demo_frames"
OUT_DIR.mkdir(parents=True, exist_ok=True)
GIF_PATH = ROOT / "reports" / "gui_demo.gif"


def grab(win: QtWidgets.QWidget, name: str) -> Path:
    pix = win.grab()
    p = OUT_DIR / f"{name}.png"
    pix.save(str(p))
    return p


def main():
    # 在线模式（窗口可见）；离屏可设 QT_QPA_PLATFORM=offscreen
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(_STYLE)
    win = MainWindow()
    win.resize(1200, 760)
    win.show()
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.4)
    QtCore.QCoreApplication.processEvents()

    frames: list[Path] = []
    frames.append(grab(win, "01_startup"))

    # 1) 加载参考与待评估（用视频，让评估过程可见）
    ref = str(ROOT / "samples" / "ref.mp4")
    dis = str(ROOT / "samples" / "dis_blur.mp4")
    win.preview_ref._set_path(ref)  # 直接调内部方法（脚本内自用）
    win.preview_dis._set_path(dis)
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.3)
    frames.append(grab(win, "02_loaded"))

    # 2) FR + SSIM
    win.mode_combo.setCurrentIndex(0)
    idx = win.algo_combo.findText("SSIM")
    win.algo_combo.setCurrentIndex(idx)
    QtCore.QCoreApplication.processEvents()
    frames.append(grab(win, "03_algo_selected"))

    # 3) 触发评估（视频会逐帧推进）
    win.stride_spin.setValue(1)
    win.max_spin.setValue(50)
    win._on_run()
    # 视频 SSIM ≈ 0.4s 完成，用更密的采样多抓几帧
    deadline = time.time() + 8.0
    fi = 4
    last_score_text = ""
    sampled_running = 0
    finished = False
    while time.time() < deadline:
        QtCore.QCoreApplication.processEvents()
        time.sleep(0.05)
        QtCore.QCoreApplication.processEvents()
        cur = win.score_label.text()
        if not finished:
            # 每 2 个循环采一帧 running，最多 8 帧
            if sampled_running < 8:
                frames.append(grab(win, f"{fi:02d}_running"))
                fi += 1
                sampled_running += 1
            if cur not in {"…", ""} and cur != last_score_text:
                last_score_text = cur
                finished = True
                time.sleep(0.4)
                QtCore.QCoreApplication.processEvents()
                frames.append(grab(win, f"{fi:02d}_done"))
                fi += 1
                time.sleep(0.5)
                QtCore.QCoreApplication.processEvents()
                frames.append(grab(win, f"{fi:02d}_final"))
                fi += 1
                break
        time.sleep(0.05)

    print(f"已采集帧数: {len(frames)}")

    # 合成 GIF：等比缩放到 800px，量化到调色板减小体积
    images: list[Image.Image] = []
    for p in frames:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        scale = 800 / w
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        images.append(im.quantize(colors=128, method=Image.MEDIANCUT))

    if images:
        # 每帧停留 0.6s；最后一帧停留 1.5s
        durations = [600] * (len(images) - 1) + [1500]
        images[0].save(
            GIF_PATH,
            save_all=True,
            append_images=images[1:],
            duration=durations,
            loop=0,
            optimize=True,
            disposal=2,
        )
        print(f"GIF 输出: {GIF_PATH}  ({GIF_PATH.stat().st_size/1024:.1f} KB)")

    # 关窗
    win.close()
    app.processEvents()


if __name__ == "__main__":
    main()
