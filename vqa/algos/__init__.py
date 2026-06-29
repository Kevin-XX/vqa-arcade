"""算法注册表：把名字映射到具体实现，方便 GUI/CLI 动态选择。"""
from __future__ import annotations

from .psnr import psnr_image, psnr_video
from .ssim import ssim_image, ssim_video
from .niqe_lite import niqe_lite_image, niqe_lite_video
from .vsfa import vsfa_image, vsfa_video
from .vsfa_video_level import vsfa_video_score, vsfa_video_image
from .vmaf_image import vmaf_image as _vmaf_image_fn
from .vmaf_video import vmaf_video_score as _vmaf_video_fn

# VMAF 图像模型用于视频：逐帧对抽样打分
def _vmaf_image_video_fn(ref_path: str, dis_path: str,
                          stride: int = 1, max_frames: int | None = None,
                          progress_callback: callable = None, **_) -> dict:
    from ..io_utils import iter_video_frames, aggregate, video_meta
    total = video_meta(ref_path).get("n_frames", 0)
    if max_frames and max_frames < total:
        total = max_frames
    import cv2, tempfile, os
    ref_iter = iter_video_frames(ref_path, stride=stride, max_frames=max_frames)
    dis_iter = iter_video_frames(dis_path, stride=stride, max_frames=max_frames)
    per_frame = []
    count = 0
    for (_, rf), (_, df) in zip(ref_iter, dis_iter):
        # 写入临时文件（VMAF 图像模型接受路径）
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tr, \
             tempfile.NamedTemporaryFile(suffix=".png", delete=False) as td:
            cv2.imwrite(tr.name, (rf * 255).astype("uint8"))
            cv2.imwrite(td.name, (df * 255).astype("uint8"))
            result = _vmaf_image_fn(tr.name, td.name)
            per_frame.append(result["score"])
            os.unlink(tr.name); os.unlink(td.name)
        count += 1
        if progress_callback and total:
            progress_callback(count, total)
    agg = aggregate(per_frame) if per_frame else aggregate([0])
    return dict(score=agg["mean"], per_frame=per_frame, unit="分", agg=agg)

# VMAF 视频模型不支持单图
def _vmaf_video_image_fn(*_, **__):
    raise ValueError("VMAF-V 是视频级模型，不支持单图评估。请使用 VMAF 或拖入视频。")

# (name, kind, callable_image, callable_video)
# kind: "FR" 全参考 / "NR" 无参考
ALGORITHMS = {
    "PSNR": dict(kind="FR", image=psnr_image, video=psnr_video,
                 desc="峰值信噪比，越大越好（dB）"),
    "SSIM": dict(kind="FR", image=ssim_image, video=ssim_video,
                 desc="结构相似度，[0,1]，越大越好"),
    "VMAF": dict(kind="FR", image=_vmaf_image_fn, video=_vmaf_image_video_fn,
                 desc="深度学习全参考（ResNet50），0~100分，越大越好"),
    "NIQE-Lite": dict(kind="NR", image=niqe_lite_image, video=niqe_lite_video,
                      desc="无参考自然度评分，越小越好（项目自实现轻量版）"),
    "VSFA": dict(kind="NR", image=vsfa_image, video=vsfa_video,
                 desc="基于 VGG16 的无参考质量评估（DMOS，越小越好）"),
    "VSFA-V": dict(kind="NR", image=vsfa_video_image, video=vsfa_video_score,
                   desc="VSFA 视频级时序模型，4帧聚合 MOS 越大越好", video_only=True),
    "VMAF-V": dict(kind="FR", image=_vmaf_video_image_fn, video=_vmaf_video_fn,
                   desc="深度学习视频全参考（ResNet18+时序），0~100分越大越好", video_only=True),
}


def list_by_kind(kind: str):
    """返回某一类（FR/NR）下的算法名称。"""
    return [k for k, v in ALGORITHMS.items() if v["kind"] == kind]
