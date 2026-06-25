"""街机分数滚动器：数字逐位翻滚，带缩放弹跳效果。

用法：
    roller = ScoreRoller()
    roller.roll_to(0.7301)   # 数字从 0 翻滚到目标值
    roller.set_label("DMOS")  # 单位标签
"""
from __future__ import annotations
import math
from PyQt5 import QtCore, QtGui, QtWidgets

_FONT_SIZE_FINAL = 38
_DIGIT_COUNT = 6             # 显示总位数（含小数点）
_TICK_INTERVAL = 40          # ms / 位
_SCALE_BOUNCE = 1.15         # 每跳缩放倍率
_BOUNCE_DURATION = 6         # 弹跳持续 tick 数

_COLORS = {
    "excellent": "#4ade80",   # 绿色：质量极好
    "good":      "#facc15",   # 黄色：质量良好
    "fair":      "#fb923c",   # 橙色：质量一般
    "poor":      "#ef4444",   # 红色：质量差
    "idle":      "#64748b",   # 灰色：待机
}


class ScoreRoller(QtWidgets.QWidget):
    """数字翻滚显示的街机分数板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self._value = 0.0
        self._target = 0.0
        self._label = ""
        self._tick = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._is_rolling = False
        self._on_done_cb = None  # 滚动完成回调
        self._color = _COLORS["idle"]

    def roll_to(self, target: float, label: str = "", callback=None):
        """开始从当前值翻滚到 target。"""
        self._target = target
        self._label = label
        self._on_done_cb = callback
        self._tick = 0
        if not self._timer.isActive():
            self._value = 0.0
            self._color = _COLORS["idle"]
            self._timer.start(_TICK_INTERVAL)
            self._is_rolling = True

    def set_instant(self, value: float, label: str = ""):
        """直接设置值，不翻滚。"""
        self._timer.stop()
        self._value = value
        self._target = value
        self._label = label
        self._is_rolling = False
        self._color = _COLORS["idle"]
        self.update()

    def _on_tick(self):
        self._tick += 1
        progress = min(1.0, self._tick / max(1, self._target * 30))
        # 使用 ease-out 曲线
        eased = 1.0 - math.pow(1.0 - progress, 3)
        self._value = self._target * eased
        self.update()
        if progress >= 1.0:
            self._value = self._target
            self._timer.stop()
            self._is_rolling = False
            self._update_color()
            self.update()
            if self._on_done_cb:
                self._on_done_cb()

    def _update_color(self):
        v = self._value
        if v <= 20:
            self._color = _COLORS["excellent"]
        elif v <= 40:
            self._color = _COLORS["good"]
        elif v <= 60:
            self._color = _COLORS["fair"]
        else:
            self._color = _COLORS["poor"]

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()

        # 显示数字
        text = f"{self._value:.4f}"
        font = QtGui.QFont("SF Mono, Menlo, monospace", _FONT_SIZE_FINAL)
        p.setFont(font)
        p.setPen(QtGui.QColor(self._color))

        # 数字弹跳缩放
        if self._is_rolling and self._tick % 3 < 2:
            scale = 1.0 + (_SCALE_BOUNCE - 1.0) * (math.sin(self._tick * 1.2) * 0.5 + 0.5)
        else:
            scale = 1.0

        p.save()
        cx, cy = w / 2, h / 2 - 10
        p.translate(cx, cy)
        p.scale(scale, scale)
        fm = QtGui.QFontMetrics(font)
        text_w = fm.horizontalAdvance(text)
        p.drawText(-text_w // 2, fm.ascent() // 2, text)
        p.restore()

        # 单位标签
        if self._label:
            unit_font = QtGui.QFont("SF Mono, Menlo, monospace", 14)
            p.setFont(unit_font)
            p.setPen(QtGui.QColor("#94a3b8"))
            p.drawText(0, int(cy + 28), w, 20, QtCore.Qt.AlignHCenter, self._label)
