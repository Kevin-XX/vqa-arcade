"""VSFA (Visual Saliency Feature Aggregation)：基于 VGG16 的无参考图像质量评估。

与 NIQE-Lite 不同，VSFA 是一个**深度学习**驱动的 NR 模型：
- 主干：VGG16（ImageNet 预训练）
- 回归头：GAP → Linear(512→512) → Linear(512→1)
- 输出：DMOS 分数（越小 = 质量越好）

权重来源：LIVE 数据集训练，通过微信接收的 VSFA_LIVE_best.pth。

与项目现有算法的差异：
- PSNR / SSIM 是 FR（全参考），需要参考图 → 必须有无损原图
- NIQE-Lite 是 NR（无参考），但基于手工特征（MSCN/锐度/噪声）
- VSFA 是 NR + 深度学习，**直接预测 DMOS**，无需手工特征设计

注意：torch / torchvision / Pillow 是本模块的额外依赖。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np

# 懒加载 torch，避免在没有 torch 时 import vqa 就报错
_torch = None
_nn = None
_models = None
_transforms = None
_Image = None


def _ensure_torch():
    global _torch, _nn, _models, _transforms, _Image
    if _torch is not None:
        return
    try:
        import torch as t
        import torch.nn as tnn
        import torchvision.models as tm
        import torchvision.transforms as ttf
        from PIL import Image as PImage
        _torch = t
        _nn = tnn
        _models = tm
        _transforms = ttf
        _Image = PImage
    except ImportError as e:
        raise ImportError(
            "VSFA 需要额外依赖：pip install torch torchvision Pillow\n"
            f"原始错误: {e}"
        )


# ---- 模型定义 ----
class _VSFAModel(_nn.Module if _nn else object):
    """VGG16 特征提取 + GAP + 全连接回归头。"""

    def __init__(self):
        super().__init__()
        vgg16 = _models.vgg16(weights=_models.VGG16_Weights.IMAGENET1K_V1)
        self.features = vgg16.features
        self.gap = _nn.AdaptiveAvgPool2d((1, 1))
        self.regressor = _nn.Sequential(
            _nn.Linear(512, 512),
            _nn.ReLU(),
            _nn.Dropout(0.5),
            _nn.Linear(512, 1),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.gap(x)
        x = x.view(x.size(0), -1)
        x = self.regressor(x)
        return x


# ---- 模型懒加载缓存 ----
_model_cache: Optional[_nn.Module] = None
_device_cache: Optional[_torch.device] = None  # type: ignore[valid-type]
_weight_path_default: Optional[str] = None


def _get_default_weight_path() -> str:
    """查找默认权重文件：优先 algos 同目录，其次项目根。"""
    global _weight_path_default
    if _weight_path_default and os.path.exists(_weight_path_default):
        return _weight_path_default
    candidates = [
        # algos 目录下
        Path(__file__).resolve().parent / "VSFA_LIVE_best.pth",
        # 项目根
        Path(__file__).resolve().parent.parent.parent / "VSFA_LIVE_best.pth",
    ]
    for p in candidates:
        if p.exists():
            _weight_path_default = str(p)
            return str(p)
    raise FileNotFoundError(
        f"找不到 VSFA 权重文件 VSFA_LIVE_best.pth，请放到 vqa/algos/ 目录下"
    )


def _get_device() -> _torch.device:  # type: ignore[valid-type]
    global _device_cache
    if _device_cache is not None:
        return _device_cache
    _ensure_torch()
    _device_cache = _torch.device("cuda" if _torch.cuda.is_available() else "cpu")
    return _device_cache


def load_vsfa_model(weight_path: Optional[str] = None) -> _nn.Module:
    """加载 VSFA 模型（带缓存，同一进程内只加载一次）。

    Args:
        weight_path: 权重 .pth 路径，默认自动查找。

    Returns:
        eval 模式下的 VSFA 模型实例。
    """
    global _model_cache
    _ensure_torch()
    if _model_cache is not None:
        return _model_cache

    if weight_path is None:
        weight_path = _get_default_weight_path()

    device = _get_device()
    # 动态补定义（因为 __init__ 内 _nn 可能还未导入）
    class VSFAModel(_nn.Module):
        def __init__(self):
            super().__init__()
            vgg16 = _models.vgg16(weights=_models.VGG16_Weights.IMAGENET1K_V1)
            self.features = vgg16.features
            self.gap = _nn.AdaptiveAvgPool2d((1, 1))
            self.regressor = _nn.Sequential(
                _nn.Linear(512, 512),
                _nn.ReLU(),
                _nn.Dropout(0.5),
                _nn.Linear(512, 1),
            )

        def forward(self, x):
            x = self.features(x)
            x = self.gap(x)
            x = x.view(x.size(0), -1)
            x = self.regressor(x)
            return x

    model = VSFAModel()
    state_dict = _torch.load(weight_path, map_location=device)
    # 兼容 DataParallel 包装的 key
    if all(k.startswith("module.") for k in state_dict.keys()):
        state_dict = {k[7:]: v for k, v in state_dict.items()}
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    _model_cache = model
    return model


def _predict_dmos(img_path: str) -> float:
    """对单张图片预测 DMOS 分数。

    Args:
        img_path: 图片路径。

    Returns:
        DMOS 浮点分数（越小质量越好）。
    """
    _ensure_torch()
    model = load_vsfa_model()
    device = _get_device()

    transform = _transforms.Compose([
        _transforms.Resize((512, 512)),
        _transforms.ToTensor(),
        _transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    img = _Image.open(img_path).convert("RGB")
    img_tensor = transform(img).unsqueeze(0).to(device)

    with _torch.no_grad():
        score = float(model(img_tensor).item())
    return score


def _quality_label(score: float) -> str:
    """根据 DMOS 分数给出质量等级描述。"""
    if score <= 20:
        return "极好（几乎无失真）"
    elif score <= 40:
        return "良好（轻微失真）"
    elif score <= 60:
        return "一般（明显失真）"
    else:
        return "差（严重失真）"


# ---- 对外统一接口（与 NIQE-Lite 对齐） ----

def vsfa_image(path: str, **_) -> dict:
    """VSFA 无参考图像评分。

    Args:
        path: 图片路径。

    Returns:
        dict: {score: float, per_frame: [float], unit: str, agg: dict, label: str}
    """
    dmos = _predict_dmos(path)
    return dict(
        score=dmos,
        per_frame=[dmos],
        unit="DMOS",
        agg={"mean": dmos, "std": 0.0, "min": dmos, "max": dmos, "n": 1},
        label=_quality_label(dmos),
    )


def vsfa_video(path: str, stride: int = 1, max_frames: int | None = None, **_) -> dict:
    """VSFA 逐帧独立评分（视频版）。

    对视频的每一帧独立跑 VSFA 推理，不做时序建模。
    这与 VSFA 论文的设计一致：VSFA 本身是单帧 NR 模型。

    Args:
        path: 视频路径。
        stride: 帧采样步长。
        max_frames: 最大帧数。

    Returns:
        dict: {score, per_frame, unit, agg, label}
    """
    _ensure_torch()
    import cv2

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频: {path}")

    per_frame: list[float] = []
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 为视频帧构建临时 PNG 路径（避免反复 decode 带来的数值差异）
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="vsfa_video_")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % stride != 0:
                frame_idx += 1
                continue
            # 写入临时图片后跑推理
            tmp_path = os.path.join(tmp_dir, f"frame_{frame_idx:06d}.png")
            cv2.imwrite(tmp_path, frame)
            dmos = _predict_dmos(tmp_path)
            per_frame.append(dmos)
            frame_idx += 1
            if max_frames and len(per_frame) >= max_frames:
                break
    finally:
        cap.release()
        # 清理临时文件
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if not per_frame:
        raise ValueError("未读取到任何帧")

    arr = np.array(per_frame)
    agg = {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "n": len(per_frame),
    }
    return dict(
        score=agg["mean"],
        per_frame=[float(v) for v in per_frame],
        unit="DMOS",
        agg=agg,
        label=_quality_label(agg["mean"]),
    )
