# VQA Arcade Machine · 视觉质量评估街机评分台

> 图像 / 视频视觉质量评估 · 街机游戏机风格交互 · 5 种算法 · Web + CLI 双通道

## 快速开始

```bash
# 安装依赖
pip install flask flask-cors numpy Pillow opencv-python-headless

# 启动 Web 版
python server.py
# → 浏览器打开 http://localhost:5100

# 命令行打分
python -m vqa.cli score samples/dis_blur.png --ref samples/ref.png --algo SSIM
```

## 5 种算法

| 算法 | 模式 | 输入 | 输出 | 核心思路 |
|------|------|------|------|---------|
| **PSNR** | FR 全参考 | 图/视频 | dB，越大越好 | 逐像素均方误差 |
| **SSIM** | FR 全参考 | 图/视频 | 0~1，越大越好 | 亮度/对比度/结构三通道对比 |
| **NIQE-Lite** | NR 无参考 | 图/视频 | ~3~30，越小越好 | 自然统计特征偏离分析（自实现轻量版） |
| **VSFA** | NR 无参考 | 图/视频 | DMOS，越小越好 | VGG16 逐帧深度学习推理 |
| **VSFA-V** | NR 无参考 | 仅视频 | MOS，越大越好 | VGG16 + 4 帧时序聚合（视频级专用） |

## 特性

- 🎮 **街机风 Web UI** — 星空背景、CRT 扫描线、像素字体、倒计时、评级揭晓、KO 特效
- 📊 **实时进度条** — SSE 流式推送、三色渐变、逐帧进度回调
- 🏆 **评级系统** — S/A/B+/B/C/D 六档，评分翻滚动画
- 🎖️ **成就系统** — 首次评测 / VSFA 首战 / 评测老手 / S 级达人 / 全能选手等 8 项
- 📈 **曲线图** — 逐帧折线 + 渐变填色 + 均值参考线
- 🔄 **FR / NR 双模式** — 全参考需原素材，无参考仅需待测文件
- 🖥 **CLI + Web 双入口** — 命令行批量分析 + 网页拖拽交互
- ⌨️ **键盘操作** — Enter/Space/Esc 全流程控制
- 📝 **使用说明面板** — 标题页和评分页均可查阅算法简介

## 目录结构

```
server.py              Flask Web 后端
web/index.html         街机前端（单文件）
web/font/              像素字体
vqa/cli.py             CLI 命令行入口
vqa/scorer.py          算法调度器
vqa/algos/             5 种算法实现 + 模型权重
vqa/gui/               PyQt5 桌面版（已冻结）
samples/               测试样例素材
scripts/               辅助脚本
tests/                 单元测试
docs/                  文档与汇报材料
```

## PyQt5 桌面版

原 PyQt5 桌面版仍在 `vqa/gui/` 中，但不再维护。启动：

```bash
pip install PyQt5
python -m vqa.gui
```

## 公网访问

已部署到 AnyDev 云环境：可通过 `http://21.91.17.10:5100` 访问（可能已过期）。

## GitHub

https://github.com/Kevin-XX/vqa-arcade
