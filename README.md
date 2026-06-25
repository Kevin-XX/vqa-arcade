# 视觉质量评估应用 (VQA Studio)

> 图像/视频视觉质量评估应用 · 专业综合设计 · 中期联调版本

## 快速开始

```bash
# 1) 安装依赖（项目已仅依赖 numpy/opencv-python(-headless)/PyQt5）
pip install --user opencv-python-headless PyQt5 numpy

# 2) 生成样例数据
python scripts/make_samples.py

# 3) 命令行打分
python -m vqa.cli list
python -m vqa.cli score samples/dis_blur.png --ref samples/ref.png --algo SSIM

# 4) 启动 GUI
python -m vqa.gui

# 5) 跑单元测试
python -m unittest tests.test_algos -v
```

## 目录

```
vqa/                算法 + GUI 主包
scripts/            生成样例 / GUI 离屏自测
samples/            参考图、失真图、参考视频、失真视频
tests/              单元测试
docs/中期汇报.md    中期汇报正文
reports/            截图与跑分 JSON
```

## 已实现算法

| 名称 | 类型 | 说明 |
|---|---|---|
| PSNR | FR | 峰值信噪比，dB，越大越好 |
| SSIM | FR | 结构相似度，[0,1]，越大越好（11×11 高斯窗） |
| NIQE-Lite | NR | 自实现轻量无参考评估器（MSCN + 锐度 + 噪声），越小越好 |
| VSFA | NR | 基于 VGG16 的无参考质量评估（DMOS 分数，越小越好），需 torch/torchvision/Pillow |

## 后续接入

VMAF（FR-Video）、官方 NIQE，详见 `docs/中期汇报.md`。
