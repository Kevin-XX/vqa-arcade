"""格斗游戏浮动文字弹幕：从分数区飞起渐隐的放大文字。

用法:
    ft = FightTextOverlay(parent)
    ft.show_text("FLAWLESS!", "#0fff50")
"""
from __future__ import annotations
import math
from PyQt5 import QtCore, QtGui, QtWidgets

_FLY_DURATION = 1800  # ms
_TICK_MS = 20

_ROOT_TEXTS = {
    "S":  ("★ FLAWLESS ★",      "#0fff50"),
    "A":  ("★ EXCELLENT ★",      "#00f0ff"),
    "B+": ("★ GREAT ★",           "#ffe600"),
    "B":  ("★ NICE ★",            "#a78bfa"),
}


class FightTextOverlay(QtWidgets.QWidget):
    """浮动大字覆盖层。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.hide()
        self._texts: list[dict] = []
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(_TICK_MS)

    def show_for_rank(self, rank: str):
        """根据评级显示对应弹幕。"""
        if rank not in _ROOT_TEXTS:
            return
        text, color = _ROOT_TEXTS[rank]
        self.show_text(text, color)
        # S 级多弹一条
        if rank == "S":
            QtCore.QTimer.singleShot(300, lambda: self.show_text("SUPREME!", "#0fff50"))

    def show_text(self, text: str, color: str):
        """添加一条浮动文字。"""
        r = self.parent().rect() if self.parent() else self.rect()
        self.setGeometry(r)
        self._texts.append({
            "text": text,
            "color": color,
            "x": self.width() // 2,
            "y": self.height() // 2 - 60,
            "life": _FLY_DURATION,
            "max_life": _FLY_DURATION,
        })
        self.show()
        self.raise_()

    def _tick(self):
        alive = []
        for t in self._texts:
            t["life"] -= _TICK_MS
            if t["life"] > 0:
                # 向上飞 + 放大
                t["y"] -= 0.6
                alive.append(t)
        self._texts = alive
        if not alive:
            self.hide()
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        for t in self._texts:
            progress = t["life"] / t["max_life"]
            alpha = int(255 * progress)
            scale = 1.0 + (1.0 - progress) * 1.2
            font_size = int(28 * scale)
            font = QtGui.QFont("Press Start 2P", font_size)
            p.setFont(font)
            c = QtGui.QColor(t["color"])
            c.setAlpha(alpha)
            p.setPen(c)
            fm = QtGui.QFontMetrics(font)
            tw = fm.horizontalAdvance(t["text"])
            p.drawText(int(t["x"] - tw // 2), int(t["y"]), t["text"])
