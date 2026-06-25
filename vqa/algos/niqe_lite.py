"""NIQE-Lite：本项目自实现的轻量无参考自然度评估器。

中期版本特意避开"加载大模型 / 预训练 PCA 参数"的依赖，转而采用
NIQE 论文中的核心思想 + 几个经验失真特征：

1. MSCN（Mean-Subtracted Contrast-Normalized）系数的全局方差与峰度——
   失真越严重通常偏离自然图像分布越远；
2. 沿水平/垂直方向的 MSCN 乘积（pairwise products），捕捉模糊与噪声；
3. 拉普拉斯响应方差（锐度），模糊→数值下降；
4. 高频差分能量（噪声估计），噪声越大→数值上升。

最终把这些特征加权聚合成一个**越小越好**的分数（typical 范围 ~3 ~ 30），
量纲与官方 NIQE 不一致，但相对排序在常见失真上具有单调性，足以验证 GUI
通路与 PPT 演示。后期接入 VSFA / 真正 NIQE 时只需替换本文件实现。
"""
from __future__ import annotations

import numpy as np
import cv2

from ..io_utils import aggregate, iter_video_frames, read_image_gray


def _mscn(img: np.ndarray, kernel_size: int = 7, sigma: float = 7 / 6) -> np.ndarray:
    img = img.astype(np.float64)
    mu = cv2.GaussianBlur(img, (kernel_size, kernel_size), sigma)
    mu_sq = cv2.GaussianBlur(img * img, (kernel_size, kernel_size), sigma)
    sigma_map = np.sqrt(np.maximum(mu_sq - mu * mu, 0.0))
    return (img - mu) / (sigma_map + 1.0 / 255.0)


def _kurtosis(x: np.ndarray) -> float:
    x = x.ravel()
    m = x.mean()
    s2 = ((x - m) ** 2).mean()
    if s2 < 1e-12:
        return 0.0
    return float(((x - m) ** 4).mean() / (s2 * s2) - 3.0)


def _laplacian_var(img: np.ndarray) -> float:
    lap = cv2.Laplacian((img * 255.0).astype(np.uint8), cv2.CV_64F)
    return float(lap.var())


def _noise_estimate(img: np.ndarray) -> float:
    """基于 Immerkaer 1996 的快速噪声估计，单位 ~标准差。"""
    H = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float64)
    conv = cv2.filter2D(img.astype(np.float64), -1, H)
    sigma = float(np.sqrt(np.pi / 2.0) * np.mean(np.abs(conv)) / 6.0)
    return sigma


def niqe_lite_value(img_gray: np.ndarray) -> float:
    """单帧 NIQE-Lite 分数；越小越好。"""
    img = img_gray
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = img.astype(np.float64)
    if img.max() > 1.5:
        img = img / 255.0

    mscn = _mscn(img)
    var_mscn = float(mscn.var())
    kurt_mscn = abs(_kurtosis(mscn))

    # pairwise products: 水平 / 垂直
    h_pp = mscn[:, :-1] * mscn[:, 1:]
    v_pp = mscn[:-1, :] * mscn[1:, :]
    pp_kurt = 0.5 * (abs(_kurtosis(h_pp)) + abs(_kurtosis(v_pp)))

    sharp = _laplacian_var(img)
    noise = _noise_estimate(img)

    # 经验组合：值越大代表越偏离自然图像
    # 锐度低 / 噪声高 / 统计量偏离自然分布 → 分数高
    sharp_term = 1.0 / np.log1p(sharp + 1.0)            # 模糊 → 大
    noise_term = noise * 80.0                            # 噪声 → 大
    stat_term = (var_mscn - 1.0) ** 2 + 0.05 * kurt_mscn + 0.05 * pp_kurt
    score = 5.0 * sharp_term + noise_term + 1.5 * stat_term
    return float(score)


def niqe_lite_image(path: str, **_) -> dict:
    img = read_image_gray(path)
    val = niqe_lite_value(img)
    return dict(score=val, per_frame=[val], unit="", agg=aggregate([val]))


def niqe_lite_video(path: str, stride: int = 1, max_frames: int | None = None,
                    progress_callback: callable = None, **_) -> dict:
    from ..io_utils import video_meta
    total = video_meta(path).get("n_frames", 0)
    if max_frames and max_frames < total:
        total = max_frames
    per_frame: list[float] = []
    count = 0
    for _, frame in iter_video_frames(path, stride=stride, max_frames=max_frames):
        per_frame.append(niqe_lite_value(frame))
        count += 1
        if progress_callback and total:
            progress_callback(count, total)
    agg = aggregate(per_frame)
    return dict(score=agg["mean"], per_frame=per_frame, unit="", agg=agg)
