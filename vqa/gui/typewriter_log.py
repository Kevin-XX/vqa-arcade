"""打字机日志：文字逐字出现，带光标闪烁效果。

替换 QPlainTextEdit 用于日志展示。
不同级别文字不同颜色：
  [ui]      → #94a3b8 灰色
  [worker]  → #60a5fa 蓝色
  [score]   → #fbbf24 黄色
  [achieve] → #f472b6 粉色
  [err]     → #f87171 红色
"""
from __future__ import annotations
from PyQt5 import QtCore, QtGui, QtWidgets

_CHAR_INTERVAL = 15   # ms / 字符
_CURSOR_BLINK = 500   # ms 光标闪烁

_COLOR_MAP = {
    "[ui]":      "#94a3b8",
    "[worker]":  "#60a5fa",
    "[score]":   "#fbbf24",
    "[achieve]": "#f472b6",
    "[err]":     "#f87171",
}


class TypewriterLog(QtWidgets.QWidget):
    """逐字打印日志 + 闪烁光标。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self._lines: list[tuple[str, str]] = []  # (prefix_color, text)
        self._queue: list[tuple[str, str]] = []
        self._char_index = 0
        self._typing = False
        self._cursor_visible = True

        self._char_timer = QtCore.QTimer(self)
        self._char_timer.timeout.connect(self._next_char)

        self._cursor_timer = QtCore.QTimer(self)
        self._cursor_timer.timeout.connect(self._toggle_cursor)
        self._cursor_timer.start(_CURSOR_BLINK)

    def append(self, text: str):
        """将一行文字加入队列，按排队顺序逐字显示。"""
        color = _COLOR_MAP.get("[ui]", "#94a3b8")
        for prefix, c in _COLOR_MAP.items():
            if text.startswith(prefix):
                color = c
                break
        self._queue.append((color, text))
        if not self._typing:
            self._start_line()

    def _start_line(self):
        if not self._queue:
            self._typing = False
            return
        self._typing = True
        color, text = self._queue.pop(0)
        self._lines.append((color, ""))
        self._current_color = color
        self._current_text = text
        self._char_index = 0
        self._cursor_visible = True
        self._char_timer.start(_CHAR_INTERVAL)

    def _next_char(self):
        self._char_index += 1
        if self._char_index <= len(self._current_text):
            self._lines[-1] = (self._current_color, self._current_text[:self._char_index])
            self.update()
        else:
            self._char_timer.stop()
            self._lines[-1] = (self._current_color, self._current_text)
            if len(self._lines) > 500:
                self._lines = self._lines[-500:]
            self.update()
            self._start_line()

    def _toggle_cursor(self):
        self._cursor_visible = not self._cursor_visible
        if self._typing or not self._lines:
            self.update()

    def clear(self):
        self._lines.clear()
        self._queue.clear()
        self._char_timer.stop()
        self._typing = False
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.TextAntialiasing)
        font = QtGui.QFont("SF Mono, Menlo, monospace", 11)
        p.setFont(font)
        fm = QtGui.QFontMetrics(font)
        line_h = fm.height() + 4

        visible_count = (self.height() - 8) // line_h
        lines_to_show = self._lines[-visible_count:] if len(self._lines) > visible_count else self._lines

        y = 8
        for color, text in lines_to_show:
            p.setPen(QtGui.QColor(color))
            p.drawText(12, y + fm.ascent(), text)
            y += line_h

        # 闪烁光标
        if self._typing and self._cursor_visible:
            p.setPen(QtGui.QColor("#22d3ee"))
            last_line = self._lines[-1][1] if self._lines else ""
            cursor_x = 12 + fm.horizontalAdvance(last_line)
            cursor_y = y - line_h
            p.drawLine(cursor_x, cursor_y + 2, cursor_x, cursor_y + line_h - 2)
