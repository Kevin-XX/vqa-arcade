"""Screen 3 · 评估画面（Gameplay）

街机风格评估界面：双预览 + 霓虹进度条 + 记分板 + 曲线 + 打字机日志。
emit finished(result) / back_to_menu 信号。
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from ..io_utils import is_image, is_video
from ..algos import ALGORITHMS
from .worker import ScoringWorker
from .curve import ScoreCurve
from .drop_preview import DropPreview
from .arcade_score import ScoreRoller
from .arcade_progress import ArcadeProgress
from .typewriter_log import TypewriterLog
from .arcade_theme import (
    C_BG, C_NEON_BLUE, C_NEON_PINK, C_GREEN_OK,
    C_YELLOW, C_DIM, C_MUTED, C_WHITE, C_RED_ERR,
    mono_font, cn_font, compute_rank,
)


class GameScreen(QtWidgets.QWidget):
    finished = QtCore.pyqtSignal(dict)
    back_to_menu = QtCore.pyqtSignal()
    countdown_requested = QtCore.pyqtSignal()
    shake_requested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self._thread: QtCore.QThread | None = None
        self._worker: ScoringWorker | None = None
        self._algo = "SSIM"
        self._kind = "FR"
        self._stride = 1
        self._max_frames = 60
        self._build_ui()

    def setup(self, algo: str, kind: str, stride: int, max_frames: int):
        """从 select_screen 传入参数。"""
        self._algo = algo
        self._kind = kind
        self._stride = stride
        self._max_frames = max_frames
        self._kind_label.setText(kind)
        self._algo_label.setText(algo)
        if kind == "NR":
            self.preview_ref.clear()
            self.preview_ref.setVisible(False)
        else:
            self.preview_ref.setVisible(True)

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 14)
        root.setSpacing(10)

        # ── 顶栏：当前模式 + 算法 + 主页按钮 ──
        top = QtWidgets.QWidget()
        th = QtWidgets.QHBoxLayout(top)
        th.setContentsMargins(0, 0, 0, 0)

        self._kind_label = QtWidgets.QLabel("FR")
        self._kind_label.setFont(mono_font(14, bold=True))
        self._kind_label.setStyleSheet(f"color: {C_NEON_BLUE};")
        th.addWidget(self._kind_label)

        sep1 = QtWidgets.QLabel("·")
        sep1.setStyleSheet(f"color: {C_DIM};")
        th.addWidget(sep1)

        self._algo_label = QtWidgets.QLabel("SSIM")
        self._algo_label.setFont(mono_font(14, bold=True))
        self._algo_label.setStyleSheet(f"color: {C_YELLOW};")
        th.addWidget(self._algo_label)

        th.addStretch(1)

        home_btn = QtWidgets.QPushButton("返回主页")
        home_btn.setObjectName("danger_btn")
        home_btn.setFixedSize(90, 30)
        home_btn.clicked.connect(self.back_to_menu.emit)
        th.addWidget(home_btn)
        root.addWidget(top)

        # ── 双预览区 ──
        preview_row = QtWidgets.QWidget()
        pr = QtWidgets.QHBoxLayout(preview_row)
        pr.setSpacing(10)

        ref_frame = self._neon_frame("参考图", C_NEON_PINK)
        ref_lay = QtWidgets.QVBoxLayout(ref_frame)
        ref_lay.setContentsMargins(8, 24, 8, 8)
        self.preview_ref = DropPreview("拖入参考图像/视频")
        ref_lay.addWidget(self.preview_ref)
        pr.addWidget(ref_frame, 1)

        dist_frame = self._neon_frame("失真图", C_NEON_BLUE)
        dist_lay = QtWidgets.QVBoxLayout(dist_frame)
        dist_lay.setContentsMargins(8, 24, 8, 8)
        self.preview_dis = DropPreview("拖入待评估输入")
        dist_lay.addWidget(self.preview_dis)
        pr.addWidget(dist_frame, 1)

        root.addWidget(preview_row, 2)

        # ── 进度条 ──
        self._progress = ArcadeProgress()
        root.addWidget(self._progress)

        # ── 记分板 ──
        sb = QtWidgets.QWidget()
        sb.setStyleSheet(f"border: 2px solid {C_NEON_BLUE}; border-radius: 6px; "
                         f"background: {C_NEON_BLUE}08;")
        sb.setFixedHeight(54)
        sb_row = QtWidgets.QHBoxLayout(sb)
        sb_row.setContentsMargins(0, 4, 0, 4)

        self._score_lbl = self._sb_item("SCORE", C_NEON_BLUE)
        self._score_val = self._sb_val(C_NEON_BLUE)
        sb_row.addWidget(self._score_lbl)
        sb_row.addWidget(self._score_val)

        self._div1 = self._sb_divider()
        sb_row.addWidget(self._div1)

        self._rank_lbl = self._sb_item("RANK", C_NEON_PINK)
        self._rank_val = self._sb_val(C_GREEN_OK)
        sb_row.addWidget(self._rank_lbl)
        sb_row.addWidget(self._rank_val)

        self._div2 = self._sb_divider()
        sb_row.addWidget(self._div2)

        self._frames_lbl = self._sb_item("帧数", C_YELLOW)
        self._frames_val = self._sb_val(C_YELLOW)
        sb_row.addWidget(self._frames_lbl)
        sb_row.addWidget(self._frames_val)

        root.addWidget(sb)

        # ── 曲线 ──
        self._curve = ScoreCurve()
        root.addWidget(self._curve, 1)

        # ── 操作按钮行 ──
        btn_row = QtWidgets.QWidget()
        bh = QtWidgets.QHBoxLayout(btn_row)
        bh.setSpacing(12)

        self._run_btn = QtWidgets.QPushButton("▶  开始评估")
        self._run_btn.setObjectName("start_btn")
        self._run_btn.setFixedSize(200, 44)
        self._run_btn.clicked.connect(self._on_run)
        bh.addWidget(self._run_btn)

        self._export_btn = QtWidgets.QPushButton("导出报告")
        self._export_btn.setObjectName("action_btn")
        self._export_btn.setFixedSize(120, 44)
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._on_export)
        bh.addWidget(self._export_btn)

        self._reset_btn = QtWidgets.QPushButton("重置")
        self._reset_btn.setObjectName("danger_btn")
        self._reset_btn.setFixedSize(80, 44)
        self._reset_btn.clicked.connect(self._on_reset)
        bh.addWidget(self._reset_btn)

        bh.addStretch(1)
        root.addWidget(btn_row)

        # ── 打字机日志 ──
        self._log = TypewriterLog()
        root.addWidget(self._log)

        self._last_result: dict | None = None

    # ------------------------------------------------------------------
    def _neon_frame(self, title: str, color: str) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setStyleSheet(
            f"border: 1px solid {color}; border-radius: 6px; "
            f"background: {color}06;")
        lbl = QtWidgets.QLabel(title)
        lbl.setFont(mono_font(10))
        lbl.setStyleSheet(f"color: {color}; border: none;")
        lbl.setParent(w)
        lbl.move(12, 6)
        return w

    def _sb_item(self, text: str, color: str) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text)
        lbl.setFont(mono_font(10))
        lbl.setStyleSheet(f"color: {color}; border: none; opacity: 0.6;")
        return lbl

    def _sb_val(self, color: str) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel("--")
        lbl.setFont(mono_font(20, bold=True))
        lbl.setStyleSheet(f"color: {color}; border: none;")
        return lbl

    def _sb_divider(self) -> QtWidgets.QLabel:
        d = QtWidgets.QLabel("")
        d.setFixedWidth(1)
        d.setStyleSheet(f"background: {C_NEON_BLUE}; border: none; opacity: 0.15;")
        return d

    def _plog(self, msg: str):
        self._log.append(msg)

    # ------------------------------------------------------------------
    def _on_run(self):
        target = self.preview_dis.path()
        if not target:
            QtWidgets.QMessageBox.warning(self, "缺少输入", "请先选择待评估的图像或视频。")
            return
        ref = self.preview_ref.path() if self._kind == "FR" else None
        if self._kind == "FR" and not ref:
            QtWidgets.QMessageBox.warning(self, "缺少参考", "FR 模式需要参考输入。")
            return

        self._pending_target = target
        self._pending_ref = ref
        self.countdown_requested.emit()
        # 倒计时完成后 arcade_main 会调用 _do_run()

    def _do_run(self):
        """倒计时结束后真正执行评估。"""
        target = self._pending_target
        ref = self._pending_ref

        self._run_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self._progress.set_range(0, 0)
        self._score_val.setText("...")
        self._rank_val.setText("--")
        self._frames_val.setText("--")
        self._plog(f"[ui] ▶ 提交任务：{self._algo} ({self._kind}) — "
                   f"{Path(target).name}"
                   + (f" ← {Path(ref).name}" if ref else ""))

        self._thread = QtCore.QThread()
        self._worker = ScoringWorker(self._algo, target, ref,
                                      stride=self._stride,
                                      max_frames=self._max_frames)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._plog)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @QtCore.pyqtSlot(int, int)
    def _on_progress(self, current: int, total: int):
        if total > 0:
            self._progress.set_range(0, total)
            self._progress.set_value(current)

    @QtCore.pyqtSlot(dict)
    def _on_finished(self, result: dict):
        self._last_result = result
        self._progress.set_complete()

        score = result["score"]
        unit = result.get("unit", "")
        agg = result["agg"]
        n = agg.get("n", 1)

        rank, rank_color = compute_rank(score, self._algo)

        self._score_val.setText(f"{score:.4f}")
        self._score_val.setStyleSheet(f"color: {C_GREEN_OK}; border: none;")
        self._rank_val.setText(rank)
        self._rank_val.setStyleSheet(f"color: {rank_color}; border: none;")
        self._frames_val.setText(str(n))

        self._curve.set_data(result["per_frame"], f"{self._algo} 逐帧得分")
        self._plog(f"[score] {self._algo}: {score:.4f} {unit}  "
                   f"评级={rank}  N={n}")
        self._run_btn.setEnabled(True)
        self._export_btn.setEnabled(True)

        # 屏幕抖动
        self.shake_requested.emit()

        # 短暂延迟后跳到结算页
        QtCore.QTimer.singleShot(1000, lambda: self.finished.emit(result))

    @QtCore.pyqtSlot(str)
    def _on_failed(self, msg: str):
        self._progress.set_range(0, 100)
        self._progress.set_value(0)
        self._run_btn.setEnabled(True)
        self._score_val.setText("ERR")
        self._score_val.setStyleSheet(f"color: {C_RED_ERR}; border: none;")
        self._plog(f"[err] 失败: {msg}")

    def _on_export(self):
        if not self._last_result:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出 JSON 报告",
            str(Path.home() / "vqa_report.json"),
            "JSON (*.json)")
        if path:
            Path(path).write_text(
                json.dumps(self._last_result, ensure_ascii=False, indent=2))
            self._plog(f"[ui] 已导出：{path}")

    def _on_reset(self):
        self._last_result = None
        self._progress.set_range(0, 100)
        self._progress.set_value(0)
        self._score_val.setText("--")
        self._score_val.setStyleSheet(f"color: {C_NEON_BLUE}; border: none;")
        self._rank_val.setText("--")
        self._rank_val.setStyleSheet(f"color: {C_NEON_PINK}; border: none;")
        self._frames_val.setText("--")
        self._curve.set_data([], "")
        self._log.clear()
        self._plog("[ui] 已重置")
