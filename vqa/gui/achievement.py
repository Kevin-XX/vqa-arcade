"""成就系统：徽章弹窗 + 成就追踪。

成就存储在内存中（不持久化），每次启动重置。
触发条件在 main_window 中检查，这里只负责弹窗显示。
"""
from __future__ import annotations
from PyQt5 import QtCore, QtGui, QtWidgets

_ACHIEVEMENTS = {
    "first_run":     ("初出茅庐",  "首次评分完成！"),
    "all_algos":     ("全家桶已集齐", "四种算法全部跑过"),
    "vsfa_first":    ("深度学习初体验", "首次使用 VSFA 模型"),
    "hundred_frames": ("帧数狂魔", "单次处理超过 100 帧"),
    "ten_runs":      ("评测老手",  "累计完成 10 次评分"),
    "all_kinds":     ("双模全开",  "FR + NR 模式都已体验"),
}

_ACHIEVEMENT_ICONS = {
    "first_run":     "✦",
    "all_algos":     "◆",
    "vsfa_first":    "◈",
    "hundred_frames": "❖",
    "ten_runs":      "★",
    "all_kinds":     "⬡",
}

SLIDE_DURATION = 400    # ms
STAY_DURATION  = 2500   # ms 停留
FADE_DURATION  = 400    # ms 淡出


class AchievementTracker:
    """轻量级成就状态机，不持久化。"""

    def __init__(self):
        self.unlocked: set[str] = set()
        self.run_count = 0
        self.algos_used: set[str] = set()
        self.kinds_used: set[str] = set()

    def unlock(self, aid: str) -> bool:
        """尝试解锁成就。返回 True 表示新解锁。"""
        if aid in self.unlocked:
            return False
        self.unlocked.add(aid)
        return True

    def check_algos(self):
        if len(self.algos_used) >= 4:
            self.unlock("all_algos")

    def check_kinds(self):
        if len(self.kinds_used) >= 2:
            self.unlock("all_kinds")

    def record_run(self, algo: str, kind: str, frames: int):
        self.run_count += 1
        self.algos_used.add(algo)
        self.kinds_used.add(kind)
        if self.run_count >= 10:
            self.unlock("ten_runs")
        self.check_algos()
        self.check_kinds()
        if frames >= 100:
            self.unlock("hundred_frames")


class AchievementPopup(QtWidgets.QWidget):
    """从右上角滑入的成就弹窗。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(280, 72)
        self.hide()
        self._queue: list[tuple[str, str, str]] = []  # (aid, title, desc)
        self._anim: QtCore.QAbstractAnimation | None = None
        self._showing = False

    def show_achievement(self, aid: str):
        if aid not in _ACHIEVEMENTS:
            return
        title, desc = _ACHIEVEMENTS[aid]
        icon = _ACHIEVEMENT_ICONS.get(aid, "★")
        if self._showing:
            self._queue.append((aid, title, desc))
            return
        self._slide_in(icon, title, desc)

    def _slide_in(self, icon: str, title: str, desc: str):
        p = self.parent().parentWidget() if self.parent() else None
        if p:
            pw = p.width()
            self.move(pw - 300, 60)

        self._showing = True
        self._current = (icon, title, desc)
        self.show()
        self.raise_()

        # 滑入
        start_geom = self.geometry()
        end_geom = QtCore.QRect(start_geom.x() - 20, start_geom.y(),
                                  start_geom.width(), start_geom.height())
        self._anim = QtCore.QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(SLIDE_DURATION)
        self._anim.setStartValue(start_geom)
        self._anim.setEndValue(end_geom)
        self._anim.setEasingCurve(QtCore.QEasingCurve.OutBack)
        self._anim.finished.connect(self._on_slide_in_done)
        self._anim.start()

    def _on_slide_in_done(self):
        QtCore.QTimer.singleShot(STAY_DURATION, self._fade_out)

    def _fade_out(self):
        self._anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(FADE_DURATION)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._on_fade_out_done)
        self._anim.start()

    def _on_fade_out_done(self):
        self.hide()
        self.setWindowOpacity(1.0)
        self._showing = False
        if self._queue:
            aid, title, desc = self._queue.pop(0)
            self._slide_in(_ACHIEVEMENT_ICONS.get(aid, "★"), title, desc)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)

        icon, title, desc = self._current if hasattr(self, "_current") else ("★", "", "")
        w, h = self.width(), self.height()

        # 背景卡片
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QColor(30, 41, 59, 240))   # #1e293b alpha
        p.drawRoundedRect(0, 0, w, h, 12, 12)

        # 左侧彩色竖条
        p.setBrush(QtGui.QColor("#f59e0b"))
        p.drawRoundedRect(0, 8, 4, h - 16, 2, 2)

        # 图标
        icon_font = QtGui.QFont("SF Mono, Menlo, monospace", 18)
        p.setFont(icon_font)
        p.setPen(QtGui.QColor("#fbbf24"))
        p.drawText(20, 30, icon)

        # 标题
        title_font = QtGui.QFont("PingFang SC, sans-serif", 13)
        title_font.setBold(True)
        p.setFont(title_font)
        p.setPen(QtGui.QColor("#f8fafc"))
        p.drawText(52, 28, title)

        # 描述
        desc_font = QtGui.QFont("PingFang SC, sans-serif", 11)
        p.setFont(desc_font)
        p.setPen(QtGui.QColor("#94a3b8"))
        p.drawText(52, 46, desc)
