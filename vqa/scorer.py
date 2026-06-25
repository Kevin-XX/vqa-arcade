"""统一调度入口：根据算法名 + 输入类型自动派发到对应实现。"""
from __future__ import annotations

from pathlib import Path

from .algos import ALGORITHMS
from .io_utils import is_image, is_video


class Scorer:
    def __init__(self, algorithm: str):
        if algorithm not in ALGORITHMS:
            raise KeyError(f"未知算法: {algorithm}; 可选 {list(ALGORITHMS)}")
        self.algorithm = algorithm
        self.spec = ALGORITHMS[algorithm]

    @property
    def kind(self) -> str:
        return self.spec["kind"]

    def score(self, target: str | Path, reference: str | Path | None = None,
              stride: int = 1, max_frames: int | None = None,
              progress_callback: callable = None) -> dict:
        target = str(target)
        if self.kind == "FR":
            if reference is None:
                raise ValueError(f"算法 {self.algorithm} 是全参考算法，需要参考输入")
            ref = str(reference)
            if is_image(target) and is_image(ref):
                fn = self.spec["image"]
                result = fn(ref, target)
            elif is_video(target) and is_video(ref):
                fn = self.spec["video"]
                result = fn(ref, target, stride=stride, max_frames=max_frames, progress_callback=progress_callback)
            else:
                raise ValueError("FR 模式下，参考与测试必须同为图像或同为视频")
        else:  # NR
            if is_image(target):
                result = self.spec["image"](target)
            elif is_video(target):
                result = self.spec["video"](target, stride=stride, max_frames=max_frames, progress_callback=progress_callback)
            else:
                raise ValueError(f"不识别的输入类型: {target}")
        result.update(algorithm=self.algorithm, kind=self.kind,
                      target=target, reference=str(reference) if reference else None)
        return result
