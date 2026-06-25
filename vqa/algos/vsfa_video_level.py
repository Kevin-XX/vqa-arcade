"""VSFA-V（视频级）：基于 VGG16 + 4 帧时序聚合的端到端视频质量评估。

与帧级 VSFA 的区别：
- 帧级：每帧独立推理 VGG16 → DMOS，视频 = 逐帧平均
- 视频级：固定采 4 帧 → 拼接 [B,4,3,512,512] → VGG16 → 时序平均 → MOS

输出 MOS 分数，越大越好（与帧级 DMOS 相反方向）。
"""
from __future__ import annotations
import os
import cv2
import numpy as np
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models
from torchvision import transforms as T

from ..io_utils import aggregate

_MODEL_DIR = Path(__file__).parent
_MODEL_PATH = _MODEL_DIR / "VSFA_Video_BEST.pth"

_IMAGENET_MEAN = [0.485, 0.455, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]

_DEVICE = None
_MODEL = None


class _VSFA(nn.Module):
    def __init__(self):
        super().__init__()
        vgg = models.vgg16(pretrained=False)
        self.features = vgg.features
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.regressor = nn.Sequential(
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 1),
        )

    def forward(self, x):
        b, n, c, h, w = x.shape
        x = x.reshape(b * n, c, h, w)
        x = self.features(x)
        x = self.pool(x)
        x = x.reshape(b, n, 512)
        x = x.mean(dim=1)
        return self.regressor(x)


def _ensure_model():
    global _DEVICE, _MODEL
    if _MODEL is None:
        _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _MODEL = _VSFA()
        _MODEL.load_state_dict(torch.load(str(_MODEL_PATH), map_location=_DEVICE, weights_only=True))
        _MODEL.to(_DEVICE)
        _MODEL.eval()


def _center_crop(frame: np.ndarray, size: int = 512) -> np.ndarray:
    h, w = frame.shape[:2]
    if h < size or w < size:
        # 尺寸不足则先等比缩放再裁
        scale = max(size / h, size / w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
        h, w = frame.shape[:2]
    top = (h - size) // 2
    left = (w - size) // 2
    return frame[top:top + size, left:left + size]


def _sample_frames(video_path: str, n: int = 4) -> np.ndarray:
    """均匀采 n 帧，中心裁剪 512×512，转 RGB。"""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        raise ValueError("无法读取视频帧数")
    indices = np.linspace(0, total - 1, n, dtype=int)
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if ok:
            frame = _center_crop(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        else:
            # fallback: 用第一帧填充
            if frames:
                frames.append(frames[-1].copy())
    cap.release()
    if not frames:
        raise ValueError(f"未能从视频中读取任何帧: {video_path}")
    while len(frames) < n:
        frames.append(frames[-1].copy())
    return np.stack(frames, axis=0)


def _predict_mos(frames: np.ndarray) -> float:
    """4 帧 → MOS 分数。"""
    _ensure_model()
    transform = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])
    tensors = [transform(f) for f in frames]  # list of [3,512,512]
    batch = torch.stack(tensors, dim=0).unsqueeze(0)  # [1,4,3,512,512]
    batch = batch.to(_DEVICE)
    with torch.no_grad():
        mos = _MODEL(batch).item()
    return float(mos)


def vsfa_video_score(path: str, **_) -> dict:
    """对单段视频输出统一格式的评分 dict。

    Returns:
        {"score": mos, "per_frame": [mos], "unit": "MOS", "agg": {...}}
    """
    frames = _sample_frames(str(path), n=4)
    mos = _predict_mos(frames)
    return dict(score=mos, per_frame=[mos], unit="MOS", agg=aggregate([mos]))


def vsfa_video_image(path: str, **_) -> dict:
    """VSFA-V 不支持单图（视频级模型需要 4 帧时序信息），回退到提示。"""
    raise ValueError("VSFA-V 是视频级模型，不支持单图评估。请使用 VSFA（帧级）或拖入视频。")
