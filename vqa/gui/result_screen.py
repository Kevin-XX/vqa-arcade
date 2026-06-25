"""Screen 4 · 结算画面（Stage Clear）

评估完成后显示：STAGE CLEAR 条幅 + 结果卡 + 操作按钮。
emit retry / back_to_menu / export 信号。
"""
from __future__ import annotations
import json, math
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from .arcade_theme import (
    C_BG, C_NEON_BLUE, C_NEON_PINK, C_GREEN_OK,
    C_YELLOW, C_MUTED, C_WHITE, C_PURPLE, C_DIM,
    mono_font, cn_font, compute_rank, pixel_font,
)


class ResultScreen(QtWidgets.QWidget):
    retry = QtCore.pyqtSignal()
    back_to_menu = QtCore.pyqtSignal()
    new_record = QtCore.pyqtSignal(float)  # emit 新纪录分数

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self._tick = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._result: dict | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)

        # ── STAGE CLEAR 条幅 ──
        self._banner = QtWidgets.QWidget()
        self._banner.setFixedSize(440, 52)
        self._banner.setStyleSheet(
            f"border: 3px solid {C_GREEN_OK}; border-radius: 8px; "
            f"background: {C_GREEN_OK}08;")
        bl = QtWidgets.QVBoxLayout(self._banner)
        bl.setAlignment(QtCore.Qt.AlignCenter)
        self._banner_text = QtWidgets.QLabel("关卡通过！")
        self._banner_text.setFont(cn_font(20, bold=True))
        self._banner_text.setStyleSheet(f"color: {C_GREEN_OK}; border: none;")
        self._banner_text.setAlignment(QtCore.Qt.AlignCenter)
        bl.addWidget(self._banner_text)
        layout.addWidget(self._banner, 0, QtCore.Qt.AlignCenter)

        # ── 结果卡片 ──
        self._card = QtWidgets.QWidget()
        self._card.setFixedSize(380, 160)
        self._card.setStyleSheet(
            f"border: 2px solid {C_NEON_BLUE}; border-radius: 8px; "
            f"background: {C_NEON_BLUE}06;")
        cl = QtWidgets.QVBoxLayout(self._card)
        cl.setAlignment(QtCore.Qt.AlignCenter)
        cl.setSpacing(6)

        self._algo_lbl = QtWidgets.QLabel("")
        self._algo_lbl.setFont(mono_font(12, bold=True))
        self._algo_lbl.setAlignment(QtCore.Qt.AlignCenter)

        self._score_big = QtWidgets.QLabel("")
        self._score_big.setFont(mono_font(36, bold=True))
        self._score_big.setAlignment(QtCore.Qt.AlignCenter)

        self._rank_big = QtWidgets.QLabel("")
        self._rank_big.setFont(mono_font(28, bold=True))
        self._rank_big.setAlignment(QtCore.Qt.AlignCenter)

        self._meta_lbl = QtWidgets.QLabel("")
        self._meta_lbl.setFont(cn_font(11))
        self._meta_lbl.setStyleSheet(f"color: {C_MUTED}; border: none;")
        self._meta_lbl.setAlignment(QtCore.Qt.AlignCenter)

        cl.addWidget(self._algo_lbl)
        cl.addWidget(self._score_big)
        cl.addWidget(self._rank_big)
        cl.addWidget(self._meta_lbl)
        layout.addWidget(self._card, 0, QtCore.Qt.AlignCenter)

        # ── 按钮行 ──
        btn_row = QtWidgets.QWidget()
        bh = QtWidgets.QHBoxLayout(btn_row)
        bh.setSpacing(16)
        bh.setAlignment(QtCore.Qt.AlignCenter)

        retry_btn = QtWidgets.QPushButton("再来一次")
        retry_btn.setObjectName("start_btn")
        retry_btn.setFixedSize(140, 44)
        retry_btn.clicked.connect(self.retry.emit)
        bh.addWidget(retry_btn)

        export_btn = QtWidgets.QPushButton("导出报告")
        export_btn.setObjectName("action_btn")
        export_btn.setFixedSize(120, 44)
        export_btn.clicked.connect(self._on_export)
        bh.addWidget(export_btn)

        menu_btn = QtWidgets.QPushButton("返回主页")
        menu_btn.setObjectName("danger_btn")
        menu_btn.setFixedSize(100, 44)
        menu_btn.clicked.connect(self.back_to_menu.emit)
        bh.addWidget(menu_btn)

        layout.addWidget(btn_row, 0, QtCore.Qt.AlignCenter)

    def show_result(self, result: dict, is_new_record: bool = False):
        """从 game_screen.finished 接收结果并展示。
        is_new_record: arcade_main 传入，表示是否刷新了历史最佳。"""
        self._result = result
        self._tick = 0
        self._timer.start(60)

        algo = result["algorithm"]
        score = result["score"]
        unit = result.get("unit", "")
        agg = result["agg"]
        rank, rank_color = compute_rank(score, algo)

        # 新纪录横幅
        if is_new_record:
            self._banner_text.setText("★  新 纪 录 ！  ★")
            self._banner_text.setStyleSheet(f"color: {C_YELLOW}; border: none;")
            self._banner.setStyleSheet(
                f"border: 3px solid {C_YELLOW}; border-radius: 8px; "
                f"background: {C_YELLOW}10;")
        else:
            self._banner_text.setText("关卡通过！")
            self._banner_text.setStyleSheet(f"color: {C_GREEN_OK}; border: none;")
            self._banner.setStyleSheet(
                f"border: 3px solid {C_GREEN_OK}; border-radius: 8px; "
                f"background: {C_GREEN_OK}08;")

        self._algo_lbl.setText(f"{algo}  ({result['kind']})")
        self._algo_lbl.setStyleSheet(f"color: {C_YELLOW}; border: none;")
        self._score_big.setText(f"{score:.4f} {unit}")
        self._score_big.setStyleSheet(f"color: {C_GREEN_OK}; border: none;")
        self._rank_big.setText(rank)
        self._rank_big.setStyleSheet(f"color: {rank_color}; border: none;")
        self._meta_lbl.setText(
            f"帧数: {agg.get('n', 1)}    耗时: {result.get('elapsed_sec', 0)}s")

    def _animate(self):
        self._tick += 1
        # 条幅呼吸动画
        alpha = 180 + int(75 * (1 + math.sin(self._tick * 0.05)) / 2)
        self._banner_text.setStyleSheet(
            f"color: rgba(15,255,80,{alpha}); border: none;")

    def _on_export(self):
        if not self._result:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "导出 JSON 报告",
            str(Path.home() / "vqa_report.json"),
            "JSON (*.json)")
        if path:
            Path(path).write_text(
                json.dumps(self._result, ensure_ascii=False, indent=2))
