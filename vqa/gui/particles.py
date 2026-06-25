"""粒子爆发特效：分数完成瞬间喷出彩色圆点，重力下落 + 渐隐。

用法：
    burst = ParticleBurst(parent_widget)
    burst.fire()                 # 以父控件中心为原点喷发
    burst.fire_at(100, 200)      # 指定位置喷发
"""
from __future__ import annotations
import random
import math
from PyQt5 import QtCore, QtGui, QtWidgets

_PARTICLE_COUNT = 40
_GRAVITY = 0.15
_LIFETIME = 50                # tick 数
_TICK_MS = 16                # ~60fps
_SPEED = 6.0
_COLORS = [
    QtGui.QColor("#fbbf24"), QtGui.QColor("#f472b6"),
    QtGui.QColor("#34d399"), QtGui.QColor("#60a5fa"),
    QtGui.QColor("#f87171"), QtGui.QColor("#a78bfa"),
    QtGui.QColor("#22d3ee"), QtGui.QColor("#fb923c"),
]


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "radius", "color")
    def __init__(self, x: float, y: float):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(_SPEED * 0.4, _SPEED)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2.0   # 初始上抛
        self.life = _LIFETIME
        self.max_life = _LIFETIME
        self.radius = random.uniform(3, 7)
        self.color = random.choice(_COLORS)


class ParticleBurst(QtWidgets.QWidget):
    """透明叠加层，喷一次粒子后自动隐藏。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.hide()
        self._particles: list[_Particle] = []
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)

    def fire_at(self, x: int, y: int):
        """在父控件坐标 (x, y) 处喷发。"""
        self._particles = [_Particle(x, y) for _ in range(_PARTICLE_COUNT)]
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self._timer.start(_TICK_MS)

    def fire(self):
        """在父控件中心喷发。"""
        if self.parent():
            r = self.parent().rect()
            self.fire_at(r.width() // 2, r.height() // 2)
        else:
            self.fire_at(100, 100)

    def _tick(self):
        alive = []
        for pt in self._particles:
            pt.x += pt.vx
            pt.y += pt.vy
            pt.vy += _GRAVITY
            pt.life -= 1
            if pt.life > 0:
                alive.append(pt)
        self._particles = alive
        self.update()
        if not alive:
            self._timer.stop()
            self.hide()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setPen(QtCore.Qt.NoPen)
        for pt in self._particles:
            alpha = int(255 * pt.life / pt.max_life)
            c = QtGui.QColor(pt.color)
            c.setAlpha(alpha)
            p.setBrush(c)
            p.drawEllipse(QtCore.QPointF(pt.x, pt.y), pt.radius, pt.radius)
