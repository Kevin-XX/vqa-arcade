"""逐帧得分曲线绘制控件，使用纯 QPainter，不依赖 matplotlib。"""
from __future__ import annotations

from typing import Sequence

from PyQt5 import QtCore, QtGui, QtWidgets


class ScoreCurve(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: list[float] = []
        self._title = "逐帧得分"
        self.setMinimumHeight(160)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    def set_data(self, values: Sequence[float], title: str = "逐帧得分"):
        self._values = list(values)
        self._title = title
        self.update()

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        rect = self.rect().adjusted(40, 20, -10, -25)
        painter.fillRect(self.rect(), QtGui.QColor("#0f172a"))

        # 网格
        pen_grid = QtGui.QPen(QtGui.QColor("#1e293b"))
        painter.setPen(pen_grid)
        for i in range(5):
            y = rect.top() + i * rect.height() / 4
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))

        # 标题与坐标
        painter.setPen(QtGui.QColor("#cbd5e1"))
        painter.drawText(rect.left(), rect.top() - 6, self._title)

        if not self._values:
            painter.setPen(QtGui.QColor("#64748b"))
            painter.drawText(rect.center() - QtCore.QPoint(40, 0), "(暂无数据)")
            return

        vmin, vmax = min(self._values), max(self._values)
        if abs(vmax - vmin) < 1e-9:
            vmin -= 0.5
            vmax += 0.5
        n = len(self._values)
        path = QtGui.QPainterPath()
        for i, v in enumerate(self._values):
            x = rect.left() + (rect.width() * i / max(n - 1, 1))
            y = rect.bottom() - (v - vmin) / (vmax - vmin) * rect.height()
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QtGui.QPen(QtGui.QColor("#22d3ee"), 2))
        painter.drawPath(path)

        # Y 轴刻度
        painter.setPen(QtGui.QColor("#94a3b8"))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        for i in range(5):
            y = rect.top() + i * rect.height() / 4
            v = vmax - (vmax - vmin) * i / 4
            painter.drawText(2, int(y) + 4, f"{v:.3f}")

        # X 轴提示
        painter.drawText(rect.left(), rect.bottom() + 18, "frame 0")
        painter.drawText(rect.right() - 60, rect.bottom() + 18, f"frame {n - 1}")
