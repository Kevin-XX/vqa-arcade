"""星空粒子背景——1980年代街机吸引模式风格。

200 颗星缓慢下行 + 亮度呼吸闪烁。
"""
from __future__ import annotations
import random, math
from PyQt5 import QtCore, QtGui, QtWidgets

_STAR_COUNT = 200
_SPEED_RANGE = (0.3, 1.8)
_TICK_MS = 50


class _Star:
    def __init__(self, w: int, h: int):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.speed = random.uniform(*_SPEED_RANGE)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(40, 255)

    def step(self, w: int, h: int):
        self.y += self.speed
        if self.y > h + 5:
            self.y = -5
            self.x = random.uniform(0, w)
        self.brightness += random.randint(-8, 8)
        self.brightness = max(30, min(255, self.brightness))


class Starfield(QtWidgets.QWidget):
    """星空粒子背景。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._stars: list[_Star] = []
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(_TICK_MS)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._stars = [_Star(self.width(), self.height())
                       for _ in range(_STAR_COUNT)]

    def showEvent(self, event):
        super().showEvent(event)
        if not self._stars:
            self._stars = [_Star(self.width(), self.height())
                           for _ in range(_STAR_COUNT)]

    def _tick(self):
        w, h = self.width(), self.height()
        for s in self._stars:
            s.step(w, h)
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtCore.Qt.NoPen)
        for s in self._stars:
            b = s.brightness
            p.setBrush(QtGui.QColor(255, 255, 255, b))
            p.drawEllipse(QtCore.QPointF(s.x, s.y), s.size, s.size)
