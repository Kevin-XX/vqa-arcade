"""GUI 主窗口 · 街机升级版

- 分数滚动器 (ScoreRoller) 替代静态数字
- 成就弹窗 (AchievementPopup) 右上角滑入
- 粒子爆发 (ParticleBurst) 完成瞬间喷彩点
- 打字机日志 (TypewriterLog) 逐字吐出
- 街机进度条 (ArcadeProgress) 分段弹跳
"""
from __future__ import annotations

import json
import time
import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

from ..algos import ALGORITHMS
from ..io_utils import is_image, is_video
from .curve import ScoreCurve
from .drop_preview import DropPreview
from .worker import ScoringWorker

from .arcade_score import ScoreRoller
from .achievement import AchievementTracker, AchievementPopup
from .particles import ParticleBurst
from .typewriter_log import TypewriterLog
from .arcade_progress import ArcadeProgress

_STYLE = """
QMainWindow, QWidget#central { background: #020617; color: #e2e8f0; }
QLabel { color: #e2e8f0; }
QGroupBox { color: #cbd5e1; border: 1px solid #1e293b; border-radius: 8px;
            margin-top: 18px; padding: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QPushButton#primary { background: #2563eb; color: white; padding: 8px 18px;
                       border-radius: 6px; font-weight: 600; }
QPushButton#primary:hover { background: #3b82f6; }
QPushButton#primary:disabled { background: #334155; color: #94a3b8; }
QComboBox, QSpinBox { background: #0f172a; color: #e2e8f0; padding: 4px 8px;
                       border: 1px solid #334155; border-radius: 6px; min-height: 22px; }
"""

_ARCADE_HEADER = """
QLabel#arcade_title {
    color: #fbbf24;
}
"""


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视觉质量评估 · VQA Studio (街机版)")
        self.resize(1200, 780)
        self._thread: QtCore.QThread | None = None
        self._worker: ScoringWorker | None = None
        self._build_ui()
        self._setup_arcade()

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QtWidgets.QWidget(objectName="central")
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ---- 标题 ----
        title = QtWidgets.QLabel("🕹 视觉质量评估 · VQA Studio")
        f = title.font()
        f.setPointSize(18)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #fbbf24;")
        root.addWidget(title)

        subtitle = QtWidgets.QLabel(
            "FR 全参考 + NR 无参考 · 多线程 · 街机风格 · 中期联调版本")
        subtitle.setStyleSheet("color: #94a3b8;")
        root.addWidget(subtitle)

        # ----- 输入区 -----
        input_box = QtWidgets.QGroupBox("📥 输入区")
        ih = QtWidgets.QHBoxLayout(input_box)
        self.preview_ref = DropPreview("参考输入 (FR 必填)")
        self.preview_dis = DropPreview("待评估输入")
        ih.addWidget(self.preview_ref)
        ih.addWidget(self.preview_dis)
        root.addWidget(input_box)

        # ----- 控制区 -----
        ctrl_box = QtWidgets.QGroupBox("🎮 控制区")
        ch = QtWidgets.QHBoxLayout(ctrl_box)
        ch.setSpacing(12)

        ch.addWidget(QtWidgets.QLabel("模式："))
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItems(["FR (全参考)", "NR (无参考)"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        ch.addWidget(self.mode_combo)

        ch.addWidget(QtWidgets.QLabel("算法："))
        self.algo_combo = QtWidgets.QComboBox()
        ch.addWidget(self.algo_combo)

        ch.addWidget(QtWidgets.QLabel("stride："))
        self.stride_spin = QtWidgets.QSpinBox()
        self.stride_spin.setRange(1, 30)
        self.stride_spin.setValue(1)
        ch.addWidget(self.stride_spin)

        ch.addWidget(QtWidgets.QLabel("最大帧："))
        self.max_spin = QtWidgets.QSpinBox()
        self.max_spin.setRange(0, 99999)
        self.max_spin.setValue(60)
        self.max_spin.setSpecialValueText("全部")
        ch.addWidget(self.max_spin)

        ch.addStretch(1)
        self.run_btn = QtWidgets.QPushButton("▶ 开始评估", objectName="primary")
        self.run_btn.clicked.connect(self._on_run)
        ch.addWidget(self.run_btn)
        root.addWidget(ctrl_box)

        self._on_mode_change(0)

        # ----- 展示区：曲线 + 进度条 + 日志 -----
        disp_box = QtWidgets.QGroupBox("📊 展示区")
        dv = QtWidgets.QVBoxLayout(disp_box)
        self.curve = ScoreCurve()
        dv.addWidget(self.curve, 1)

        self.arcade_progress = ArcadeProgress()
        dv.addWidget(self.arcade_progress)

        self.typewriter = TypewriterLog()
        dv.addWidget(self.typewriter)
        root.addWidget(disp_box, 1)

        # ----- 结果区 -----
        result_box = QtWidgets.QGroupBox("🏆 结果区")
        rh = QtWidgets.QHBoxLayout(result_box)

        # 分数滚动器
        self.score_roller = ScoreRoller()
        rh.addWidget(self.score_roller, 2)

        # 统计详情（保持原有 HTML 样式）
        self.detail_label = QtWidgets.QLabel("拖入文件开始评估 ▼")
        self.detail_label.setStyleSheet("color: #94a3b8;")
        self.detail_label.setWordWrap(True)
        self.detail_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        rh.addWidget(self.detail_label, 3)

        self.export_btn = QtWidgets.QPushButton("导出 JSON")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export)
        rh.addWidget(self.export_btn, 0, QtCore.Qt.AlignTop)
        root.addWidget(result_box)

        self._last_result: dict | None = None
        self.statusBar().showMessage("🕹 就绪 — 拖入图像/视频开始体验街机评分！")

    # ------------------------------------------------------------------
    def _setup_arcade(self):
        self.achievement_tracker = AchievementTracker()
        self._ach_popup = AchievementPopup(self)
        self._particles = ParticleBurst(self.centralWidget())

    # ------------------------------------------------------------------
    def _on_mode_change(self, _idx: int):
        kind = "FR" if self.mode_combo.currentIndex() == 0 else "NR"
        self.algo_combo.clear()
        for name, spec in ALGORITHMS.items():
            if spec["kind"] == kind:
                self.algo_combo.addItem(name)
        self.preview_ref.setEnabled(kind == "FR")
        if kind == "NR":
            self.preview_ref.clear()

    def _log(self, msg: str):
        self.typewriter.append(msg)

    # ------------------------------------------------------------------
    def _on_run(self):
        target = self.preview_dis.path()
        if not target:
            QtWidgets.QMessageBox.warning(self, "缺少输入", "请先选择待评估的图像或视频。")
            return
        algo = self.algo_combo.currentText()
        kind = ALGORITHMS[algo]["kind"]
        ref = self.preview_ref.path() if kind == "FR" else None
        if kind == "FR" and not ref:
            QtWidgets.QMessageBox.warning(self, "缺少参考", "FR 模式需要参考输入。")
            return
        if kind == "FR":
            if not ((is_image(target) and is_image(ref))
                    or (is_video(target) and is_video(ref))):
                QtWidgets.QMessageBox.warning(self, "类型不一致", "FR 模式下参考与测试需同为图像或视频。")
                return

        max_frames = self.max_spin.value() or None
        stride = self.stride_spin.value()

        self.run_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.arcade_progress.set_range(0, 0)   # busy 模式
        self.arcade_progress.set_value(0)
        self.score_roller.set_instant(0.0)
        self.detail_label.setText("评估中...")
        self._log(f"[ui] ▶ 提交任务：{algo} ({kind}) — {Path(target).name}"
                  + (f" ← {Path(ref).name}" if ref else ""))

        self._thread = QtCore.QThread()
        self._worker = ScoringWorker(algo, target, ref, stride=stride,
                                      max_frames=max_frames)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self._log)
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
            self.arcade_progress.set_range(0, total)
            self.arcade_progress.set_value(current)
        else:
            self.arcade_progress.set_range(0, 0)

    @QtCore.pyqtSlot(dict)
    def _on_finished(self, result: dict):
        self._last_result = result
        algo = result["algorithm"]
        kind = result["kind"]
        unit = result.get("unit", "")
        agg = result["agg"]
        n_frames = agg.get("n", 1)
        elapsed = result.get("elapsed_sec", 0)

        self.arcade_progress.set_range(0, n_frames)
        self.arcade_progress.set_complete()

        self.run_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # --- 分数滚动动画 ---
        self.score_roller.roll_to(
            result["score"],
            label=unit,
            callback=lambda: self._on_roll_done(result)
        )

        better = "↑ 越大越好" if algo in {"PSNR", "SSIM"} else "↓ 越小越好"
        self.detail_label.setText(
            f"算法 <b>{algo}</b> ({kind})  · {better}<br>"
            f"逐帧 N = {agg['n']} · mean = {agg['mean']:.4f} · std = {agg['std']:.4f}<br>"
            f"min = {agg['min']:.4f} · max = {agg['max']:.4f} · 耗时 {elapsed}s"
        )
        self.curve.set_data(result["per_frame"], f"{algo} 逐帧得分")
        self._log(f"[score] {algo}: {result['score']:.4f} {unit}  (N={n_frames}, {elapsed:.1f}s)")

    def _on_roll_done(self, result: dict):
        """分数滚动完成后触发粒子 + 成就。"""
        algo = result["algorithm"]
        kind = result["kind"]
        n_frames = result["agg"].get("n", 1)

        # 粒子爆发在分数区
        roller_pos = self.score_roller.mapToParent(
            QtCore.QPoint(self.score_roller.width() // 2,
                          self.score_roller.height() // 2))
        self._particles.fire_at(roller_pos.x(), roller_pos.y())

        # --- 成就系统 ---
        tracker = self.achievement_tracker
        # 首次运行
        if tracker.unlock("first_run"):
            self._ach_popup.show_achievement("first_run")
            self._log("[achieve] ★ 成就解锁：初出茅庐")
        # VSFA 首次
        if algo == "VSFA" and tracker.unlock("vsfa_first"):
            self._ach_popup.show_achievement("vsfa_first")
            self._log("[achieve] ◈ 成就解锁：深度学习初体验")
        # 记录本次运行
        tracker.record_run(algo, kind, n_frames)
        if tracker.run_count == 10:
            self._ach_popup.show_achievement("ten_runs")
            self._log("[achieve] ★ 成就解锁：评测老手")
        if len(tracker.algos_used) >= 4 and tracker.unlock("all_algos"):
            self._ach_popup.show_achievement("all_algos")
            self._log("[achieve] ◆ 成就解锁：全家桶已集齐")
        if len(tracker.kinds_used) >= 2 and tracker.unlock("all_kinds"):
            self._ach_popup.show_achievement("all_kinds")
            self._log("[achieve] ⬡ 成就解锁：双模全开")
        if n_frames >= 100 and tracker.unlock("hundred_frames"):
            self._ach_popup.show_achievement("hundred_frames")
            self._log("[achieve] ❖ 成就解锁：帧数狂魔")

        self.statusBar().showMessage(f"🕹 {algo} 评分完成！", 5000)

    @QtCore.pyqtSlot(str)
    def _on_failed(self, msg: str):
        self.arcade_progress.set_range(0, 100)
        self.arcade_progress.set_value(0)
        self.run_btn.setEnabled(True)
        self.score_roller.set_instant(0.0)
        self.detail_label.setText(f"<span style='color:#f87171'>失败: {msg}</span>")
        self._log(f"[err] 失败: {msg}")

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
            self._log(f"[ui] 已导出：{path}")


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(_STYLE + _ARCADE_HEADER)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
