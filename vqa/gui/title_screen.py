"""Screen 1 · 标题画面（Attract Mode v3）

星空粒子背景 + 像素标题字母逐字弹入 + 霓虹光晕 + "PRESS START" 闪烁。
"""
from __future__ import annotations
import math
from PyQt5 import QtCore, QtGui, QtWidgets
from .arcade_theme import (
    C_BG, C_NEON_BLUE, C_NEON_PINK, C_GREEN_OK,
    C_YELLOW, C_MUTED, C_WHITE,
    mono_font, cn_font, pixel_font, neon_glow,
)
from .starfield import Starfield

_ALGO_BADGES = [
    ("SSIM",  C_YELLOW), ("PSNR",  C_YELLOW),
    ("NIQE",  C_YELLOW), ("VSFA",  C_NEON_PINK),
]


class TitleScreen(QtWidgets.QWidget):
    start_clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self._tick = 0
        self._letter_tick = 0
        self._letters_shown = 0
        self._blink_on = True

        # ── 星空背景 ──
        self._stars = Starfield(self)

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(22)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addStretch(2)

        # ── 标题框 ──
        title_box = QtWidgets.QWidget()
        title_box.setFixedSize(480, 90)
        title_box.setStyleSheet(
            f"border: 3px solid {C_NEON_BLUE}; border-radius: 8px; "
            f"background: {C_NEON_BLUE}08;")
        neon_glow(title_box, C_NEON_BLUE, 20)

        tl = QtWidgets.QVBoxLayout(title_box)
        tl.setAlignment(QtCore.Qt.AlignCenter)
        tl.setSpacing(2)

        self._title_main = QtWidgets.QLabel("VQA ARCADE MACHINE")
        self._title_main.setFont(pixel_font(11))
        self._title_main.setStyleSheet(f"color: {C_NEON_BLUE}; border: none;")
        self._title_main.setAlignment(QtCore.Qt.AlignCenter)

        self._title_sub = QtWidgets.QLabel("视觉质量评估 · 街机评分台")
        self._title_sub.setFont(cn_font(12))
        self._title_sub.setStyleSheet(f"color: {C_NEON_BLUE}; border: none;")
        self._title_sub.setAlignment(QtCore.Qt.AlignCenter)

        tl.addWidget(self._title_main)
        tl.addWidget(self._title_sub)
        layout.addWidget(title_box, 0, QtCore.Qt.AlignCenter)

        # ── 算法徽章 ──
        badge_row = QtWidgets.QWidget()
        bh = QtWidgets.QHBoxLayout(badge_row)
        bh.setSpacing(14)
        bh.setAlignment(QtCore.Qt.AlignCenter)
        for name, color in _ALGO_BADGES:
            badge = QtWidgets.QLabel(name)
            badge.setFont(pixel_font(7))
            badge.setStyleSheet(f"color: {color}; border: 2px solid {color}; "
                                f"padding: 4px 14px;")
            badge.setAlignment(QtCore.Qt.AlignCenter)
            bh.addWidget(badge)
        layout.addWidget(badge_row, 0, QtCore.Qt.AlignCenter)

        # ── PRESS START ──
        self._start_label = QtWidgets.QLabel("PRESS  START")
        self._start_label.setFont(pixel_font(14))
        self._start_label.setStyleSheet(f"color: {C_GREEN_OK};")
        self._start_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._start_label)

        self._start_btn = QtWidgets.QPushButton("▶  开始游戏")
        self._start_btn.setObjectName("start_btn")
        self._start_btn.setFixedSize(280, 60)
        self._start_btn.setFont(pixel_font(9))
        self._start_btn.clicked.connect(self.start_clicked.emit)
        layout.addWidget(self._start_btn, 0, QtCore.Qt.AlignCenter)

        # ── 高分 ──
        self._hi_label = QtWidgets.QLabel("HI-SCORE")
        self._hi_label.setFont(pixel_font(8))
        self._hi_label.setStyleSheet(f"color: {C_MUTED};")
        self._hi_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._hi_label)

        self._hi_score = QtWidgets.QLabel("--")
        self._hi_score.setFont(pixel_font(16))
        self._hi_score.setStyleSheet(f"color: {C_NEON_PINK};")
        self._hi_score.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self._hi_score)

        layout.addStretch(2)

        footer = QtWidgets.QLabel("v2.0 · 深圳大学 · 2026")
        footer.setFont(cn_font(10))
        footer.setStyleSheet(f"color: {C_MUTED};")
        footer.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(footer)

    def _animate(self):
        self._tick += 1
        # PRESS START 闪烁
        self._blink_on = (self._tick % 40) < 28
        alpha = 255 if self._blink_on else 40
        self._start_label.setStyleSheet(f"color: rgba(15,255,80,{alpha});")
        self.update()

    def set_high_score(self, score: float, unit: str = ""):
        self._hi_score.setText(f"{score:.4f} {unit}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._stars.setGeometry(self.rect())

    def showEvent(self, event):
        super().showEvent(event)
        self._stars.setGeometry(self.rect())
        self._stars.show()
