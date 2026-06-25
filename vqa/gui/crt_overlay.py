"""CRT 扫描线全屏覆盖层：模拟老式显像管显示器的扫描线 + 暗角效果。

透明悬浮在所有页面之上，paintEvent 绘制水平暗线 + 四角渐变暗角。
"""
from __future__ import annotations
from PyQt5 import QtCore, QtGui, QtWidgets
from .arcade_theme import C_BG

_SCAN_LINE_SPACING = 4
_SCAN_LINE_ALPHA = 12   # 0-255，扫描线透明度
_VIGNETTE_ALPHA = 40    # 暗角强度


class CRTOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._tick = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def _animate(self):
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        w, h = self.width(), self.height()

        # 静态扫描线（固定位置，不滚动）
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(0, 0, 0, _SCAN_LINE_ALPHA))
        for y in range(0, h, _SCAN_LINE_SPACING):
            p.drawRect(0, y, w, 1)

        # 四角暗角（径向渐变）
        p.setPen(QtCore.Qt.NoPen)
        vignette_r = max(w, h) * 0.7
        gradient = QtGui.QRadialGradient(w / 2, h / 2, vignette_r)
        gradient.setColorAt(0.0, QtGui.QColor(0, 0, 0, 0))
        gradient.setColorAt(0.7, QtGui.QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QtGui.QColor(0, 0, 0, _VIGNETTE_ALPHA))
        p.setBrush(gradient)
        p.drawRect(0, 0, w, h)
