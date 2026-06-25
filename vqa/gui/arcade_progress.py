"""街机进度条：分段色块从左到右点亮，每块亮起时弹一下。

Busy 模式下显示脉冲扫描线（max=0 时自动激活）。
"""
from __future__ import annotations
from PyQt5 import QtCore, QtGui, QtWidgets

_SEGMENT_COUNT = 20
_BOUNCE_TIMER_MS = 16
_BAR_HEIGHT = 14
_COLOR_START = QtGui.QColor("#22d3ee")
_COLOR_END   = QtGui.QColor("#a78bfa")
_BUSY_COLOR  = QtGui.QColor("#6366f1")  # 紫蓝色扫描线


class ArcadeProgress(QtWidgets.QWidget):
    """分段弹跳进度条。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(_BAR_HEIGHT + 12)
        self._value = 0
        self._maximum = 100
        self._busy = False
        self._busy_pos = 0.0     # 0~1 扫描线位置
        self._busy_dir = 1
        self._seg_boosts = [0.0] * _SEGMENT_COUNT
        self._tick = 0

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(_BOUNCE_TIMER_MS)

    def set_range(self, minimum: int, maximum: int):
        self._maximum = maximum
        self._busy = (maximum == 0)

    def set_value(self, value: int):
        if self._busy:
            return
        old_active = int(self._value / max(1, self._maximum) * _SEGMENT_COUNT)
        self._value = min(value, self._maximum)
        new_active = int(self._value / max(1, self._maximum) * _SEGMENT_COUNT)
        for i in range(old_active, new_active):
            if 0 <= i < _SEGMENT_COUNT:
                self._seg_boosts[i] = 1.0
        self.update()

    def set_complete(self):
        self._busy = False
        self._value = self._maximum
        for i in range(_SEGMENT_COUNT):
            self._seg_boosts[i] = 1.0
        self.update()

    def _on_tick(self):
        self._tick += 1
        changed = False

        # busy 脉冲扫描线
        if self._busy:
            self._busy_pos += 0.04 * self._busy_dir
            if self._busy_pos >= 1.0:
                self._busy_pos = 1.0
                self._busy_dir = -1
            elif self._busy_pos <= 0.0:
                self._busy_pos = 0.0
                self._busy_dir = 1
            changed = True

        # 段弹跳衰减
        for i in range(_SEGMENT_COUNT):
            if self._seg_boosts[i] > 0.01:
                self._seg_boosts[i] *= 0.82
                changed = True

        if changed:
            self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width() - 4
        seg_w = w / _SEGMENT_COUNT
        gap = 2
        active = 0 if self._busy else int(self._value / max(1, self._maximum) * _SEGMENT_COUNT)

        for i in range(_SEGMENT_COUNT):
            x = 2 + i * seg_w
            sw = max(seg_w - gap, 2)
            h = _BAR_HEIGHT + self._seg_boosts[i] * 8
            dy = (self.height() - h) // 2

            # busy 模式：扫描线扫到的段点亮
            if self._busy:
                seg_center = (i + 0.5) / _SEGMENT_COUNT
                dist = abs(seg_center - self._busy_pos)
                if dist < 0.15:
                    alpha_pct = 1.0 - dist / 0.15
                    r = int(_BUSY_COLOR.red() * alpha_pct + 0x33 * (1 - alpha_pct))
                    g = int(_BUSY_COLOR.green() * alpha_pct + 0x41 * (1 - alpha_pct))
                    b = int(_BUSY_COLOR.blue() * alpha_pct + 0x55 * (1 - alpha_pct))
                    p.setPen(QtCore.Qt.NoPen)
                    p.setBrush(QtGui.QColor(r, g, b))
                else:
                    p.setPen(QtCore.Qt.NoPen)
                    p.setBrush(QtGui.QColor("#334155"))
            elif i < active:
                t = i / max(1, _SEGMENT_COUNT - 1)
                cr = _COLOR_START.red()   + int((_COLOR_END.red()   - _COLOR_START.red())   * t)
                cg = _COLOR_START.green() + int((_COLOR_END.green() - _COLOR_START.green()) * t)
                cb = _COLOR_START.blue()  + int((_COLOR_END.blue()  - _COLOR_START.blue())  * t)
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QColor(cr, cg, cb))
            else:
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QColor("#334155"))

            p.drawRoundedRect(x, dy, sw, h, 3, 3)
