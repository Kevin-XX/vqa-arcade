"""Screen 2 · 选模式 + 选算法

FR / NR 两张卡片左右排列，选中高亮。下方算法标签行 + 参数。
emit confirmed(algo, kind, stride, max_frames) 信号。
"""
from __future__ import annotations
from PyQt5 import QtCore, QtGui, QtWidgets
from ..algos import ALGORITHMS
from .arcade_theme import (
    C_BG, C_NEON_BLUE, C_NEON_PINK, C_GREEN_OK,
    C_YELLOW, C_DIM, C_MUTED, C_WHITE,
    mono_font, cn_font,
)


class SelectScreen(QtWidgets.QWidget):
    confirmed = QtCore.pyqtSignal(str, str, int, int)  # algo, kind, stride, max_frames

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self._kind = "FR"
        self._algo = "SSIM"
        self._stride = 1
        self._max_frames = 60
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)

        # ── 标题 ──
        title = QtWidgets.QLabel("选择模式")
        title.setFont(cn_font(22, bold=True))
        title.setStyleSheet(f"color: {C_YELLOW};")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # ── FR / NR 两张卡片 ──
        card_row = QtWidgets.QWidget()
        ch = QtWidgets.QHBoxLayout(card_row)
        ch.setSpacing(24)
        ch.setAlignment(QtCore.Qt.AlignCenter)

        self._fr_card = self._make_card("FR  MODE", "全参考模式", "PSNR  ·  SSIM",
                                         C_NEON_BLUE, lambda: self._select_kind("FR"))
        self._nr_card = self._make_card("NR  MODE", "无参考模式", "NIQE-Lite  ·  VSFA",
                                         C_NEON_PINK, lambda: self._select_kind("NR"))

        ch.addWidget(self._fr_card)
        ch.addWidget(self._nr_card)
        layout.addWidget(card_row)

        # ── 算法标签行 ──
        self._algo_row = QtWidgets.QWidget()
        self._refresh_algos()
        layout.addWidget(self._algo_row, 0, QtCore.Qt.AlignCenter)

        # ── 参数行 ──
        param_row = QtWidgets.QWidget()
        ph = QtWidgets.QHBoxLayout(param_row)
        ph.setSpacing(16)
        ph.setAlignment(QtCore.Qt.AlignCenter)

        ph.addWidget(self._label("步长"))
        self._stride_spin = QtWidgets.QSpinBox()
        self._stride_spin.setRange(1, 30)
        self._stride_spin.setValue(1)
        self._stride_spin.valueChanged.connect(lambda v: setattr(self, '_stride', v))
        ph.addWidget(self._stride_spin)

        ph.addWidget(self._label("最大帧数"))
        self._max_spin = QtWidgets.QSpinBox()
        self._max_spin.setRange(0, 99999)
        self._max_spin.setValue(60)
        self._max_spin.setSpecialValueText("全部")
        self._max_spin.valueChanged.connect(lambda v: setattr(self, '_max_frames', v or None))
        ph.addWidget(self._max_spin)
        layout.addWidget(param_row)

        # ── 开打按钮 ──
        self._fight_btn = QtWidgets.QPushButton("▶  开打！")
        self._fight_btn.setObjectName("start_btn")
        self._fight_btn.setFixedSize(240, 50)
        self._fight_btn.clicked.connect(
            lambda: self.confirmed.emit(self._algo, self._kind,
                                        self._stride, self._max_frames))
        layout.addWidget(self._fight_btn, 0, QtCore.Qt.AlignCenter)

        # 初始选中 FR
        self._select_kind("FR")

    # ------------------------------------------------------------------
    def _label(self, text: str) -> QtWidgets.QLabel:
        lbl = QtWidgets.QLabel(text)
        lbl.setFont(cn_font(11))
        lbl.setStyleSheet(f"color: {C_MUTED};")
        return lbl

    def _make_card(self, title: str, sub: str, algo_list: str,
                   color: str, handler) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        w.setFixedSize(220, 120)
        w.setCursor(QtCore.Qt.PointingHandCursor)
        w.mousePressEvent = lambda _: handler()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setAlignment(QtCore.Qt.AlignCenter)
        lay.setSpacing(6)

        t = QtWidgets.QLabel(title)
        t.setFont(cn_font(16, bold=True))
        t.setStyleSheet(f"color: {color}; border: none;")
        t.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(t)

        s = QtWidgets.QLabel(sub)
        s.setFont(cn_font(11))
        s.setStyleSheet(f"color: {color}; border: none; opacity: 0.6;")
        s.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(s)

        a = QtWidgets.QLabel(algo_list)
        a.setFont(mono_font(10))
        a.setStyleSheet(f"color: {color}; border: none; opacity: 0.4;")
        a.setAlignment(QtCore.Qt.AlignCenter)
        lay.addWidget(a)

        w._title_lbl = t
        w._sub_lbl = s
        w._algo_lbl = a
        w._color = color
        w.setStyleSheet(f"border: 1px solid {C_DIM}; border-radius: 8px; "
                        f"background: transparent;")
        return w

    def _select_kind(self, kind: str):
        self._kind = kind
        for card, c in [(self._fr_card, "FR"), (self._nr_card, "NR")]:
            if c == kind:
                card.setStyleSheet(
                    f"border: 2px solid {card._color}; border-radius: 8px; "
                    f"background: {card._color}10;")
            else:
                card.setStyleSheet(
                    f"border: 1px solid {C_DIM}; border-radius: 8px; "
                    f"background: transparent;")
        self._refresh_algos()

    def _refresh_algos(self):
        if not hasattr(self, '_algo_row'):
            return
        lay = self._algo_row.layout()
        if lay is None:
            lay = QtWidgets.QHBoxLayout(self._algo_row)
            lay.setSpacing(10)
            lay.setAlignment(QtCore.Qt.AlignCenter)
        else:
            while lay.count():
                item = lay.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        row = lay
        for name, spec in ALGORITHMS.items():
            if spec["kind"] != self._kind:
                continue
            btn = QtWidgets.QPushButton(name)
            btn.setFont(mono_font(11, bold=True))
            btn.setFixedSize(100, 34)
            btn.clicked.connect(lambda _, n=name: self._pick_algo(n))
            row.addWidget(btn)
        self._apply_algo_style()

    def _pick_algo(self, algo: str):
        self._algo = algo
        self._apply_algo_style()

    def _apply_algo_style(self):
        layout = self._algo_row.layout()
        if not layout:
            return
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if isinstance(w, QtWidgets.QPushButton):
                if w.text() == self._algo:
                    w.setStyleSheet(
                        f"color: {C_GREEN_OK}; border: 2px solid {C_GREEN_OK}; "
                        f"border-radius: 4px; padding: 4px 12px; "
                        f"background: {C_GREEN_OK}10;")
                else:
                    w.setStyleSheet(
                        f"color: {C_YELLOW}; border: 1px solid {C_YELLOW}; "
                        f"border-radius: 4px; padding: 4px 12px; "
                        f"background: transparent;")
