"""闪屏过渡 + 倒计时覆盖层。

用法:
    overlay = FlashOverlay(parent)
    overlay.flash()           # CRT 雪花噪点闪屏 100ms
    overlay.countdown(cb)     # 3-2-1-GO! 动画，完成后调用 cb
"""
from __future__ import annotations
from PyQt5 import QtCore, QtGui, QtWidgets

_COUNTDOWN_MS = 600


class FlashOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.hide()

        self._mode = "idle"      # idle | glitch | countdown
        self._glitch_frames = 0
        self._glitch_alpha = 0
        self._cd_count = 3
        self._cd_text = ""
        self._cd_done = None
        self._bounce = 0

        self._glitch_timer = QtCore.QTimer(self)
        self._glitch_timer.timeout.connect(self._on_glitch_tick)

        self._cd_timer = QtCore.QTimer(self)
        self._cd_timer.timeout.connect(self._on_cd_tick)

        self._bounce_timer = QtCore.QTimer(self)
        self._bounce_timer.timeout.connect(self._on_bounce_tick)

    def _resize(self):
        p = self.parent()
        if p:
            self.setGeometry(p.rect())

    # ── 噪点闪屏 ──
    def flash(self):
        self._resize()
        self._mode = "glitch"
        # 仅做轻量切页闪屏，不再绘制雪花噪点
        self._glitch_frames = 3
        self._glitch_alpha = 70
        self._glitch_timer.stop()
        self.show()
        self.raise_()
        self._glitch_timer.start(16)

    def _on_glitch_tick(self):
        self._glitch_frames -= 1
        self._glitch_alpha = max(0, self._glitch_alpha - 24)
        if self._glitch_frames <= 0:
            self._glitch_timer.stop()
            self._mode = "idle"
            self._glitch_alpha = 0
            self.hide()
        self.update()

    # ── 倒计时 ──
    def countdown(self, on_done):
        self._resize()
        self._mode = "countdown"
        self._cd_count = 3
        self._cd_text = "3"
        self._cd_done = on_done
        self._bounce = 12
        self._cd_timer.stop()
        self._bounce_timer.stop()
        self.show()
        self.raise_()
        self._cd_timer.start(_COUNTDOWN_MS)
        self._bounce_timer.start(16)

    def _on_cd_tick(self):
        self._cd_count -= 1
        if self._cd_count > 0:
            self._cd_text = str(self._cd_count)
            self._bounce = 12
        else:
            self._cd_timer.stop()
            self._cd_text = "GO!"
            self._bounce = 16
            QtCore.QTimer.singleShot(500, self._finish_cd)

    def _finish_cd(self):
        self._bounce_timer.stop()
        self._mode = "idle"
        self._cd_text = ""
        self.hide()
        if self._cd_done:
            self._cd_done()

    def _on_bounce_tick(self):
        self._bounce = max(0, self._bounce - 1.5)
        if self._bounce <= 0:
            self._bounce_timer.stop()
        self.update()

    # ── 绘制 ──
    def paintEvent(self, event):
        if self._mode == "idle":
            return

        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        if self._mode == "glitch":
            self._draw_glitch(p)
        elif self._mode == "countdown":
            self._draw_countdown(p)

    def _draw_glitch(self, p: QtGui.QPainter):
        # 轻量闪屏：仅短暂暗化 + 1 条柔和扫描线，避免雪花噪点
        w, h = self.width(), self.height()
        p.setPen(QtCore.Qt.NoPen)

        # 全屏暗化快速衰减
        p.setBrush(QtGui.QColor(0, 0, 0, self._glitch_alpha))
        p.drawRect(0, 0, w, h)

        # 一条轻微高亮线（营造 CRT 切页感）
        y = int(h * 0.35 + (3 - self._glitch_frames) * h * 0.18)
        y = max(0, min(h - 2, y))
        p.setBrush(QtGui.QColor(255, 255, 255, max(0, self._glitch_alpha - 30)))
        p.drawRect(0, y, w, 2)

    def _draw_countdown(self, p: QtGui.QPainter):
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 200))
        font = QtGui.QFont("Press Start 2P, SF Mono, Menlo", int(72 + self._bounce))
        p.setFont(font)
        p.setPen(QtGui.QColor("#0fff50"))
        fm = QtGui.QFontMetrics(font)
        tw = fm.horizontalAdvance(self._cd_text)
        p.drawText((self.width() - tw) // 2,
                   (self.height() + fm.ascent()) // 2, self._cd_text)
