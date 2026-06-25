"""图像/视频视觉质量评估应用 (Visual Quality Assessment, VQA)。

提供：
- 全参考 (FR) 算法：PSNR、SSIM
- 无参考 (NR) 算法：NIQE-Lite（MSCN + AGGD 统计 + 锐度/噪声）
- 统一调度器 :class:`Scorer`，对图像与视频均可逐帧评分
- PyQt5 GUI 与 CLI 两种入口
"""

__version__ = "0.1.0-mid"
