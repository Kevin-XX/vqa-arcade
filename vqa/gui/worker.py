"""PyQt5 工作线程：把打分计算推到后台线程，避免 UI 卡顿。

UI 通过信号 :pyqtSignal 回收 (progress / log / finished)。
"""
from __future__ import annotations

from PyQt5 import QtCore

from ..scorer import Scorer


class ScoringWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)        # current, total (帧数级)
    log = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(dict)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, algorithm: str, target: str,
                 reference: str | None = None,
                 stride: int = 1,
                 max_frames: int | None = None):
        super().__init__()
        self.algorithm = algorithm
        self.target = target
        self.reference = reference
        self.stride = stride
        self.max_frames = max_frames
        self._abort = False

    @QtCore.pyqtSlot()
    def run(self):
        try:
            scorer = Scorer(self.algorithm)
            self.log.emit(f"[worker] 启动 {self.algorithm} ({scorer.kind}) 模式")
            result = scorer.score(self.target, self.reference,
                                   stride=self.stride,
                                   max_frames=self.max_frames)
            n = len(result.get("per_frame", []))
            self.progress.emit(n, n)
            self.log.emit(f"[worker] 完成，平均得分 = {result['score']:.4f}")
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
