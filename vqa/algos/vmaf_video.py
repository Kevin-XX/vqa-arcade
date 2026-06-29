"""VMAF 视频质量评估（深度学习版）：ResNet18 帧编码 + 时序池化全参考模型。

架构：均匀抽 8 帧 → 共享 ResNet18 提取特征 → 
ref/diff/dist 时序平均池化 → 拼接 → 全连接 → JND 0~1。

输出 quality_score = 100 - JND*100，越大越好。
"""
from __future__ import annotations
import os
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

from ..io_utils import aggregate

_MODEL_DIR = Path(__file__).parent
_CHECKPOINT = _MODEL_DIR / "VMAF_video.pth"

NUM_FRAMES = 8
IMG_SIZE = 224
_MEAN = torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(3, 1, 1)
_STD  = torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(3, 1, 1)

_DEVICE = None
_MODEL = None


class _FrameEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        backbone = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        self.extractor = nn.Sequential(
            backbone.conv1, backbone.bn1, backbone.relu, backbone.maxpool,
            backbone.layer1, backbone.layer2, backbone.layer3, backbone.layer4,
            backbone.avgpool,
        )
        self.out_dim = 512

    def forward(self, x):
        return self.extractor(x).flatten(1)


class _VideoQualityModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = _FrameEncoder()
        d = self.encoder.out_dim
        self.fusion = nn.Sequential(
            nn.Linear(d * 3, 512), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(512, 128), nn.ReLU(),
            nn.Linear(128, 1), nn.Sigmoid(),
        )

    def forward(self, ref, dist):
        B, T, C, H, W = ref.shape
        ref = ref.view(B * T, C, H, W)
        dist = dist.view(B * T, C, H, W)
        f_ref = self.encoder(ref).view(B, T, -1)
        f_dist = self.encoder(dist).view(B, T, -1)
        diff = torch.abs(f_ref - f_dist)
        f_ref = f_ref.mean(dim=1)
        f_dist = f_dist.mean(dim=1)
        diff = diff.mean(dim=1)
        x = torch.cat([f_ref, f_dist, diff], dim=1)
        return self.fusion(x).squeeze(1)


def _ensure_model():
    global _DEVICE, _MODEL
    if _MODEL is None:
        _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not _CHECKPOINT.exists():
            raise FileNotFoundError(f"VMAF 视频模型权重不存在: {_CHECKPOINT}")
        _MODEL = _VideoQualityModel().to(_DEVICE)
        ckpt = torch.load(str(_CHECKPOINT), map_location=_DEVICE, weights_only=False)
        sd = ckpt.get("model_state_dict", ckpt)
        _MODEL.load_state_dict(sd)
        _MODEL.eval()


def _sample_frames(path: str, num: int = NUM_FRAMES) -> torch.Tensor:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"视频打开失败: {path}")
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        raise ValueError(f"视频帧数异常: {path}")
    if total >= num:
        indices = np.linspace(0, total - 1, num, dtype=int)
    else:
        indices = list(range(total)) + [total - 1] * (num - total)
        indices = np.array(indices[:num], dtype=int)

    frames = []
    last = None
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok or frame is None:
            if last is not None:
                frame = last
            else:
                continue
        else:
            last = frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
        t = torch.from_numpy(rgb.astype(np.float32) / 255.0).permute(2, 0, 1).float()
        t = (t - _MEAN) / _STD
        frames.append(t)
    cap.release()
    if not frames:
        raise ValueError(f"无有效帧: {path}")
    while len(frames) < num:
        frames.append(frames[-1].clone())
    return torch.stack(frames[:num], dim=0)  # [T, 3, H, W]


def vmaf_video_score(ref_path: str, dis_path: str, **_) -> dict:
    _ensure_model()
    ref_t = _sample_frames(ref_path).unsqueeze(0).to(_DEVICE)
    dis_t = _sample_frames(dis_path).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        jnd = float(_MODEL(ref_t, dis_t).item())
    dmos = jnd * 100.0
    score = 100.0 - dmos
    level = _quality_level(score)
    return dict(score=score, per_frame=[score], unit="分",
                agg=aggregate([score]), jnd=jnd, dmos=dmos, label=level)


def _quality_level(s: float) -> str:
    if s >= 85: return "优秀"
    elif s >= 70: return "良好"
    elif s >= 55: return "一般"
    elif s >= 40: return "较差"
    return "很差"
