"""街机主窗口 v4 HYPER：QStackedWidget + CRT + 噪点闪屏 + 倒计时 + 音效 + 弹幕 + 键盘 + 抖动

果汁效果：
- 切页时 CRT 雪花噪点闪屏 100ms
- 评估前 "3-2-1-GO!" 像素大字倒计时 + 哔哔声
- 分数完成瞬间窗口抖动 + 胜利旋律
- 新纪录超长旋律 + 金色条幅 + 弹幕
- 键盘 Enter/Space 全局操控
- 结算页浮动格斗弹幕（FLAWLESS/EXCELLENT）
"""
from __future__ import annotations
import json, sys, random
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from .title_screen import TitleScreen
from .select_screen import SelectScreen
from .game_screen import GameScreen
from .result_screen import ResultScreen
from .crt_overlay import CRTOverlay
from .flash_overlay import FlashOverlay
from .achievement import AchievementTracker, AchievementPopup
from .particles import ParticleBurst
from .fight_text import FightTextOverlay
from .chip_sounds import ChipSounds
from .arcade_theme import GLOBAL_QSS, compute_rank

_SCORE_FILE = Path.home() / ".vqa_arcade_scores.json"


class ArcadeMain(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VQA ARCADE MACHINE · HYPER")
        self.resize(1050, 700)

        self.setStyleSheet(GLOBAL_QSS)
        self._sound = ChipSounds()

        self._stack = QtWidgets.QStackedWidget()
        self._stack.setObjectName("page")
        self.setCentralWidget(self._stack)

        self._title = TitleScreen()
        self._select = SelectScreen()
        self._game = GameScreen()
        self._result = ResultScreen()

        self._stack.addWidget(self._title)
        self._stack.addWidget(self._select)
        self._stack.addWidget(self._game)
        self._stack.addWidget(self._result)

        self._crt = CRTOverlay(self._stack)
        self._flash = FlashOverlay(self._stack)
        self._fight_text = FightTextOverlay(self._stack)
        self._ach_tracker = AchievementTracker()
        self._ach_popup = AchievementPopup(self._stack)
        self._particles = ParticleBurst(self._stack)

        self._title.start_clicked.connect(self._go_to_select)
        self._select.confirmed.connect(self._go_to_game)
        self._game.finished.connect(self._go_to_result)
        self._game.back_to_menu.connect(self._go_to_title)
        self._game.countdown_requested.connect(self._on_countdown_requested)
        self._game.shake_requested.connect(self._shake)
        self._result.retry.connect(self._go_to_game_retry)
        self._result.back_to_menu.connect(self._go_to_title)

        self._hi_scores = self._load_scores()
        self._update_hi_display()
        self._stack.setCurrentIndex(0)

        # 自动返回计时器
        self._auto_return_timer = QtCore.QTimer(self)
        self._auto_return_timer.timeout.connect(self._go_to_title)
        self._auto_return_countdown = 0

    # ── 键盘事件 ──
    def keyPressEvent(self, event):
        key = event.key()
        idx = self._stack.currentIndex()
        if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space):
            if idx == 0:
                self._go_to_select()
            elif idx == 3:
                self._go_to_game_retry()
        elif key == QtCore.Qt.Key_Escape:
            if idx in (1, 2):
                self._go_to_title()
            elif idx == 3:
                self._go_to_title()
        else:
            super().keyPressEvent(event)

    # ── 页面切换 ──
    def _switch_page(self, idx: int):
        self._flash.flash()
        self._stack.setCurrentIndex(idx)
        self._auto_return_timer.stop()
        # 结算页 15 秒自动返回
        if idx == 3:
            self._auto_return_countdown = 15
            self._auto_return_timer.start(15000)

    def _go_to_title(self):
        self._sound.click()
        self._switch_page(0)
        self._update_hi_display()

    def _go_to_select(self):
        self._sound.coin()
        self._switch_page(1)

    def _go_to_game(self, algo, kind, stride, max_frames):
        self._sound.click()
        self._game.setup(algo, kind, stride, max_frames)
        self._switch_page(2)

    def _go_to_game_retry(self):
        self._sound.click()
        self._switch_page(2)

    # ── 倒计时 ──
    def _on_countdown_requested(self):
        def _tick_sound():
            self._sound.tick()
        def _go_sound():
            self._sound.go()

        self._sound.tick()
        QtCore.QTimer.singleShot(600, _tick_sound)
        QtCore.QTimer.singleShot(1200, _tick_sound)
        QtCore.QTimer.singleShot(1800, _go_sound)
        self._flash.countdown(on_done=lambda: self._game._do_run())

    # ── 结果 ──
    def _go_to_result(self, result):
        score = result["score"]
        algo = result["algorithm"]
        rank, _ = compute_rank(score, algo)
        old_best = self._hi_scores[0]["score"] if self._hi_scores else 0
        is_new = score > old_best

        self._result.show_result(result, is_new_record=is_new)
        self._switch_page(3)

        # 音效
        if is_new:
            self._sound.super_victory()
        else:
            self._sound.victory()

        # 弹幕
        QtCore.QTimer.singleShot(400, lambda: self._fight_text.show_for_rank(rank))

        # 粒子
        self._particles.fire_at(525, 380)
        if is_new or rank == "S":
            QtCore.QTimer.singleShot(300, lambda: self._particles.fire_at(525, 280))
            QtCore.QTimer.singleShot(600, lambda: self._particles.fire_at(525, 480))

        # 存分
        self._hi_scores.append({
            "score": score, "algo": algo,
            "unit": result.get("unit", ""), "kind": result["kind"],
        })
        self._hi_scores.sort(key=lambda x: x["score"], reverse=True)
        self._hi_scores = self._hi_scores[:10]
        self._save_scores()

        # 成就
        kind = result["kind"]
        n = result["agg"].get("n", 1)
        at = self._ach_tracker
        if at.unlock("first_run"):
            self._ach_popup.show_achievement("first_run")
        if algo == "VSFA" and at.unlock("vsfa_first"):
            self._ach_popup.show_achievement("vsfa_first")
        at.record_run(algo, kind, n)

    # ── 抖动 ──
    def _shake(self):
        orig = self.pos()
        for phase in range(3):
            dx = random.randint(-10, 10)
            dy = random.randint(-8, 8)
            QtCore.QTimer.singleShot(phase * 40, lambda x=dx, y=dy: self.move(orig.x() + x, orig.y() + y))
        QtCore.QTimer.singleShot(130, lambda: self.move(orig))

    # ── 高分 ──
    def _load_scores(self):
        try:
            return json.loads(_SCORE_FILE.read_text())
        except Exception:
            return []

    def _save_scores(self):
        _SCORE_FILE.write_text(json.dumps(self._hi_scores, ensure_ascii=False))

    def _update_hi_display(self):
        if self._hi_scores:
            s = self._hi_scores[0]
            self._title.set_high_score(s["score"], s.get("unit", ""))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        g = self._stack.geometry()
        self._crt.setGeometry(g)
        self._flash.setGeometry(g)
        self._fight_text.setGeometry(g)

    def showEvent(self, event):
        super().showEvent(event)
        g = self._stack.geometry()
        self._crt.setGeometry(g)
        self._crt.raise_()
        self._flash.setGeometry(g)
        self._flash.hide()           # 确保初始隐藏
        self._fight_text.setGeometry(g)
        self._fight_text.hide()
        # 重新 raise 顺序：flash/fight 在最下层，CRT 在最上层
        self._flash.lower()
        self._fight_text.lower()
        self._crt.raise_()
