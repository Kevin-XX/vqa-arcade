"""PSNR：峰值信噪比（Peak Signal-to-Noise Ratio）。

对像素差的均方误差取对数得到 dB，越大表示越接近参考。
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from ..io_utils import (
    aggregate,
    iter_video_frames,
    read_image_gray,
)


def psnr_value(ref: np.ndarray, dis: np.ndarray, data_range: float = 1.0) -> float:
    """单帧 PSNR。输入应为 float32 ∈ [0, 1]，shape 一致。"""
    if ref.shape != dis.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {dis.shape}")
    mse = float(np.mean((ref.astype(np.float64) - dis.astype(np.float64)) ** 2))
    if mse <= 1e-12:
        return 100.0  # 完全相同
    return 10.0 * np.log10((data_range ** 2) / mse)


def psnr_image(ref_path: str, dis_path: str) -> dict:
    ref = read_image_gray(ref_path)
    dis = read_image_gray(dis_path)
    if ref.shape != dis.shape:
        # 适配尺寸（GUI 上传图常常分辨率略有差异）
        import cv2
        dis = cv2.resize(dis, (ref.shape[1], ref.shape[0]))
    val = psnr_value(ref, dis)
    return dict(score=val, per_frame=[val], unit="dB", agg=aggregate([val]))


def psnr_video(ref_path: str, dis_path: str,
               stride: int = 1,
               max_frames: int | None = None,
               progress_callback: callable = None) -> dict:
    """逐帧 PSNR，按 (ref, dis) 同步取帧。"""
    import cv2
    from ..io_utils import video_meta
    total = video_meta(ref_path).get("n_frames", 0)
    if max_frames and max_frames < total:
        total = max_frames
    refs = iter_video_frames(ref_path, stride=stride, max_frames=max_frames)
    diss = iter_video_frames(dis_path, stride=stride, max_frames=max_frames)
    per_frame: list[float] = []
    count = 0
    for (i, r), (_, d) in zip(refs, diss):
        if r.shape != d.shape:
            d = cv2.resize(d, (r.shape[1], r.shape[0]))
        per_frame.append(psnr_value(r, d))
        count += 1
        if progress_callback and total:
            progress_callback(count, total)
    agg = aggregate(per_frame)
    return dict(score=agg["mean"], per_frame=per_frame, unit="dB", agg=agg)
