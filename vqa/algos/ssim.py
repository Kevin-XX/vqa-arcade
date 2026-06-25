"""SSIM：结构相似度（Structural Similarity Index）。

按 Wang 等 2004 论文的卷积形式实现，使用 11x11 高斯窗口。
返回每帧/整张图的 mean SSIM。
"""
from __future__ import annotations

import numpy as np
import cv2

from ..io_utils import aggregate, iter_video_frames, read_image_gray


def _gauss_kernel_2d(size: int = 11, sigma: float = 1.5) -> np.ndarray:
    k = cv2.getGaussianKernel(size, sigma)
    return (k @ k.T).astype(np.float64)


_K1, _K2 = 0.01, 0.03
_KERNEL = _gauss_kernel_2d()


def _filter(img: np.ndarray) -> np.ndarray:
    return cv2.filter2D(img, -1, _KERNEL, borderType=cv2.BORDER_REFLECT)


def ssim_value(ref: np.ndarray, dis: np.ndarray, data_range: float = 1.0) -> float:
    """单帧 mean SSIM，输入 float32/64 ∈ [0, data_range]。"""
    if ref.shape != dis.shape:
        raise ValueError(f"shape mismatch: {ref.shape} vs {dis.shape}")
    x = ref.astype(np.float64)
    y = dis.astype(np.float64)
    c1 = (_K1 * data_range) ** 2
    c2 = (_K2 * data_range) ** 2

    mu_x = _filter(x)
    mu_y = _filter(y)
    mu_x2 = mu_x * mu_x
    mu_y2 = mu_y * mu_y
    mu_xy = mu_x * mu_y
    sigma_x2 = _filter(x * x) - mu_x2
    sigma_y2 = _filter(y * y) - mu_y2
    sigma_xy = _filter(x * y) - mu_xy

    num = (2 * mu_xy + c1) * (2 * sigma_xy + c2)
    den = (mu_x2 + mu_y2 + c1) * (sigma_x2 + sigma_y2 + c2)
    ssim_map = num / den
    return float(ssim_map.mean())


def ssim_image(ref_path: str, dis_path: str) -> dict:
    ref = read_image_gray(ref_path)
    dis = read_image_gray(dis_path)
    if ref.shape != dis.shape:
        dis = cv2.resize(dis, (ref.shape[1], ref.shape[0]))
    val = ssim_value(ref, dis)
    return dict(score=val, per_frame=[val], unit="", agg=aggregate([val]))


def ssim_video(ref_path: str, dis_path: str,
               stride: int = 1,
               max_frames: int | None = None,
               progress_callback: callable = None) -> dict:
    from ..io_utils import video_meta
    total = video_meta(ref_path).get("n_frames", 0)
    if max_frames and max_frames < total:
        total = max_frames
    refs = iter_video_frames(ref_path, stride=stride, max_frames=max_frames)
    diss = iter_video_frames(dis_path, stride=stride, max_frames=max_frames)
    per_frame: list[float] = []
    count = 0
    for (_, r), (_, d) in zip(refs, diss):
        if r.shape != d.shape:
            d = cv2.resize(d, (r.shape[1], r.shape[0]))
        per_frame.append(ssim_value(r, d))
        count += 1
        if progress_callback and total:
            progress_callback(count, total)
    agg = aggregate(per_frame)
    return dict(score=agg["mean"], per_frame=per_frame, unit="", agg=agg)
