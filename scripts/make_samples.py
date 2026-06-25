"""生成 samples/ 下用于测试与展示的样例数据：
- ref.png：合成自然纹理参考图
- dis_blur.png：高斯模糊
- dis_noise.png：加性高斯噪声
- dis_jpeg.jpg：JPEG 重压缩
- ref.mp4 / dis_blur.mp4：5 秒短视频
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
SAMPLES.mkdir(parents=True, exist_ok=True)


def make_reference(h: int = 360, w: int = 480) -> np.ndarray:
    rng = np.random.default_rng(20260519)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # 多频率正弦叠加 + 渐变 + 噪点细节，保留可压缩纹理
    img = (
        0.5 + 0.25 * np.sin(2 * np.pi * xx / 32) * np.cos(2 * np.pi * yy / 48)
        + 0.15 * np.sin(2 * np.pi * (xx + yy) / 90)
        + 0.05 * rng.standard_normal((h, w)).astype(np.float32)
    )
    img = np.clip(img, 0.0, 1.0)
    img8 = (img * 255).astype(np.uint8)
    color = cv2.applyColorMap(img8, cv2.COLORMAP_VIRIDIS)
    # 加几个高对比度色块，便于看 SSIM
    cv2.rectangle(color, (40, 40), (160, 160), (250, 250, 250), -1)
    cv2.circle(color, (360, 240), 60, (20, 20, 220), -1)
    cv2.putText(color, "VQA REF", (180, 320), cv2.FONT_HERSHEY_SIMPLEX,
                1.4, (0, 0, 0), 4, cv2.LINE_AA)
    return color


def main() -> None:
    print(f"[gen] writing samples to {SAMPLES}")
    ref = make_reference()
    cv2.imwrite(str(SAMPLES / "ref.png"), ref)

    blur = cv2.GaussianBlur(ref, (15, 15), 4.0)
    cv2.imwrite(str(SAMPLES / "dis_blur.png"), blur)

    rng = np.random.default_rng(7)
    noisy = ref.astype(np.float32) + rng.normal(0, 25, ref.shape).astype(np.float32)
    noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    cv2.imwrite(str(SAMPLES / "dis_noise.png"), noisy)

    cv2.imwrite(str(SAMPLES / "dis_jpeg.jpg"), ref,
                [int(cv2.IMWRITE_JPEG_QUALITY), 12])

    # 视频：5 秒，10 fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    h, w = ref.shape[:2]
    fps, n_frames = 10, 50

    def write_video(path: Path, transform):
        vw = cv2.VideoWriter(str(path), fourcc, fps, (w, h))
        for i in range(n_frames):
            shift = int(2 * np.sin(i / 6.0))
            M = np.float32([[1, 0, shift], [0, 1, 0]])
            base = cv2.warpAffine(ref, M, (w, h), borderMode=cv2.BORDER_REFLECT)
            vw.write(transform(base, i))
        vw.release()

    write_video(SAMPLES / "ref.mp4", lambda f, i: f)
    write_video(SAMPLES / "dis_blur.mp4",
                lambda f, i: cv2.GaussianBlur(f, (11, 11), 3.0))
    write_video(SAMPLES / "dis_noise.mp4",
                lambda f, i: np.clip(f.astype(np.float32) +
                                     np.random.default_rng(i).normal(0, 18, f.shape),
                                     0, 255).astype(np.uint8))
    print("[gen] done.")


if __name__ == "__main__":
    main()
