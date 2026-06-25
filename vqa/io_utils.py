"""图像/视频读写工具，统一返回灰度 float32 ndarray，范围 [0, 1]。

避免 GUI / 算法各自实现一套读图逻辑。
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple

import cv2
import numpy as np


IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
VID_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMG_EXT


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in VID_EXT


def read_image_gray(path: str | Path) -> np.ndarray:
    """读取灰度图像，返回 float32 ∈ [0, 1]。"""
    p = str(path)
    img = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"无法读取图像: {p}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray.astype(np.float32) / 255.0


def read_image_bgr(path: str | Path) -> np.ndarray:
    p = str(path)
    img = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"无法读取图像: {p}")
    return img


def iter_video_frames(path: str | Path,
                      stride: int = 1,
                      max_frames: int | None = None) -> Iterator[Tuple[int, np.ndarray]]:
    """逐帧迭代视频，返回 (frame_index, gray_float32)。"""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频: {path}")
    idx = 0
    yielded = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                yield idx, gray
                yielded += 1
                if max_frames is not None and yielded >= max_frames:
                    break
            idx += 1
    finally:
        cap.release()


def video_meta(path: str | Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频: {path}")
    try:
        return dict(
            width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            fps=float(cap.get(cv2.CAP_PROP_FPS) or 0.0),
            n_frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0),
        )
    finally:
        cap.release()


def aggregate(scores: list[float]) -> dict:
    """对逐帧得分做基本聚合。"""
    if not scores:
        return dict(mean=float("nan"), std=0.0, min=float("nan"), max=float("nan"), n=0)
    arr = np.asarray(scores, dtype=np.float64)
    return dict(
        mean=float(arr.mean()),
        std=float(arr.std(ddof=0)),
        min=float(arr.min()),
        max=float(arr.max()),
        n=int(arr.size),
    )
