"""算法注册表：把名字映射到具体实现，方便 GUI/CLI 动态选择。"""
from __future__ import annotations

from .psnr import psnr_image, psnr_video
from .ssim import ssim_image, ssim_video
from .niqe_lite import niqe_lite_image, niqe_lite_video
from .vsfa import vsfa_image, vsfa_video
from .vsfa_video_level import vsfa_video_score, vsfa_video_image

# (name, kind, callable_image, callable_video)
# kind: "FR" 全参考 / "NR" 无参考
ALGORITHMS = {
    "PSNR": dict(kind="FR", image=psnr_image, video=psnr_video,
                 desc="峰值信噪比，越大越好（dB）"),
    "SSIM": dict(kind="FR", image=ssim_image, video=ssim_video,
                 desc="结构相似度，[0,1]，越大越好"),
    "NIQE-Lite": dict(kind="NR", image=niqe_lite_image, video=niqe_lite_video,
                      desc="无参考自然度评分，越小越好（项目自实现轻量版）"),
    "VSFA": dict(kind="NR", image=vsfa_image, video=vsfa_video,
                 desc="基于 VGG16 的无参考质量评估（DMOS，越小越好）"),
    "VSFA-V": dict(kind="NR", image=vsfa_video_image, video=vsfa_video_score,
                   desc="VSFA 视频级时序模型，4帧聚合 MOS 越大越好", video_only=True),
}


def list_by_kind(kind: str):
    """返回某一类（FR/NR）下的算法名称。"""
    return [k for k, v in ALGORITHMS.items() if v["kind"] == kind]
