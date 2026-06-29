"""VMAF 图像质量评估（深度学习版）：ResNet50 Siamese 全参考模型。

架构：参考图+失真图拼接为 [B,6,224,224] → 共享 ResNet50 → 
ref特征 | dist特征 | abs差异 → 全连接回归 → DMOS 0~1。

输出 quality_score = 100 - DMOS*100，越大越好。
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
_CHECKPOINT = _MODEL_DIR / "VMAF_image.pth"

_MEAN = [0.485, 0.456, 0.406, 0.485, 0.456, 0.406]
_STD  = [0.229, 0.224, 0.225, 0.229, 0.224, 0.225]
IMG_SIZE = 224

_DEVICE = None
_MODEL = None


class _VMAFNet(nn.Module):
    """ResNet50 双分支 + 特征差异回归。"""
    def __init__(self, dropout_rate=0.2, freeze_stages=5):
        super().__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
        self.backbone = nn.Sequential(
            resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool,
            resnet.layer1, resnet.layer2, resnet.layer3, resnet.layer4,
            resnet.avgpool,
        )
        self.regressor = nn.Sequential(
            nn.Linear(2048 * 3, 512), nn.LayerNorm(512), nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(512, 128), nn.LayerNorm(128), nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate * 0.5),
            nn.Linear(128, 1), nn.Sigmoid(),
        )

    def forward(self, x):
        ref = x[:, :3, :, :]
        dist = x[:, 3:, :, :]
        f_ref = self.backbone(ref).flatten(1)
        f_dist = self.backbone(dist).flatten(1)
        f_diff = torch.abs(f_ref - f_dist)
        feat = torch.cat([f_ref, f_dist, f_diff], dim=1)
        return self.regressor(feat).squeeze(1)


def _ensure_model():
    global _DEVICE, _MODEL
    if _MODEL is None:
        _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if not _CHECKPOINT.exists():
            raise FileNotFoundError(f"VMAF 图像模型权重不存在: {_CHECKPOINT}")
        ckpt = torch.load(str(_CHECKPOINT), map_location=_DEVICE, weights_only=False)
        config = ckpt.get("config", {})
        _MODEL = _VMAFNet(
            dropout_rate=config.get("dropout_rate", 0.2),
            freeze_stages=config.get("freeze_stages", 5),
        ).to(_DEVICE)
        _MODEL.load_state_dict(ckpt["state_dict"])
        _MODEL.eval()


def _preprocess(ref_path: str, dist_path: str) -> torch.Tensor:
    ref_bgr = cv2.imread(ref_path)
    dist_bgr = cv2.imread(dist_path)
    if ref_bgr is None:
        raise ValueError(f"参考图读取失败: {ref_path}")
    if dist_bgr is None:
        raise ValueError(f"失真图读取失败: {dist_path}")
    ref_rgb = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2RGB)
    dist_rgb = cv2.cvtColor(dist_bgr, cv2.COLOR_BGR2RGB)
    h, w = dist_rgb.shape[:2]
    if ref_rgb.shape[:2] != (h, w):
        ref_rgb = cv2.resize(ref_rgb, (w, h), interpolation=cv2.INTER_AREA)
    ref_rgb = cv2.resize(ref_rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    dist_rgb = cv2.resize(dist_rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    ref_t = ref_rgb.astype(np.float32) / 255.0
    dist_t = dist_rgb.astype(np.float32) / 255.0
    concat = np.concatenate([ref_t, dist_t], axis=2)  # (224, 224, 6)
    concat = concat.transpose(2, 0, 1)  # (6, 224, 224)
    tensor = torch.from_numpy(concat).float()
    mean = torch.tensor(_MEAN, dtype=torch.float32).view(6, 1, 1)
    std = torch.tensor(_STD, dtype=torch.float32).view(6, 1, 1)
    tensor = (tensor - mean) / std
    return tensor.unsqueeze(0)  # (1, 6, 224, 224)


def vmaf_image(ref_path: str, dis_path: str, **_) -> dict:
    _ensure_model()
    inp = _preprocess(ref_path, dis_path).to(_DEVICE)
    with torch.no_grad():
        dmos_norm = float(_MODEL(inp).item())
    dmos = dmos_norm * 100.0
    score = 100.0 - dmos
    level = _quality_level(score)
    return dict(score=score, per_frame=[score], unit="分",
                agg=aggregate([score]), dmos=dmos, label=level)


def _quality_level(s: float) -> str:
    if s >= 85: return "优秀"
    elif s >= 70: return "良好"
    elif s >= 55: return "一般"
    elif s >= 40: return "较差"
    return "很差"
