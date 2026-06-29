# VQA Arcade Machine - 项目知识库

## 项目概述
视觉质量评估街机评分台 - 图像/视频视觉质量评估工具，街机游戏机风格交互，5 种算法，Web + CLI 双通道。
学术项目：专业综合设计课程，小组成员江子路/曹天诚/常家硕/徐凯文，指导老师周飞。

## 技术栈
- **后端**: Flask (Python)，端口 5100，server.py
- **前端**: 单文件 HTML (web/index.html)，街机 CRT 风格，纯 vanilla JS
- **核心算法**: Python + OpenCV + NumPy，VSFA 需要 PyTorch + torchvision
- **CLI**: argparse 命令行入口 (vqa/cli.py)
- **GUI**: PyQt5 (vqa/gui/)，已冻结不再维护
- **部署**: AnyDev 云环境 (http://21.91.17.10:5100，可能已过期)
- **GitHub**: https://github.com/Kevin-XX/vqa-arcade

## 五种算法

| 算法 | 模式 | 输入 | 输出 | 说明 |
|------|------|------|------|------|
| PSNR | FR 全参考 | 图/视频 | dB↑ | 逐像素均方误差 |
| SSIM | FR 全参考 | 图/视频 | 0~1↑ | 11x11高斯窗卷积，Wang 2004 |
| NIQE-Lite | NR 无参考 | 图/视频 | ~3~30↓ | 自实现轻量版，MSCN+AGGD+锐度+噪声 |
| VSFA | NR 无参考 | 图/视频 | DMOS↓ | VGG16(GAP→512→512→1)，权重VSFA_LIVE_best.pth |
| VSFA-V | NR 无参考 | 仅视频 | MOS↑ | VGG16+4帧时序聚合，权重VSFA_Video_BEST.pth |

## 架构分层

```
server.py          → Flask Web 后端 (SSE流式推送进度)
web/index.html     → 街机前端 (单文件，星空/CRT扫描线/像素字体)
vqa/
  cli.py           → CLI 命令行 (python -m vqa.cli score ...)
  scorer.py        → 统一调度器 Scorer 类，按算法+输入类型派发
  io_utils.py      → 图像/视频 I/O (read_image_gray, iter_video_frames, aggregate)
  algos/
    __init__.py    → 算法注册表 ALGORITHMS dict
    psnr.py        → PSNR 实现 (image/video)
    ssim.py        → SSIM 实现 (image/video)
    niqe_lite.py   → NIQE-Lite 实现 (image/video)
    vsfa.py        → VSFA 帧级 (image/video)
    vsfa_video_level.py → VSFA-V 视频级 (video_only)
    VSFA_LIVE_best.pth     → VSFA 模型权重
    VSFA_Video_BEST.pth    → VSFA-V 模型权重
  gui/             → PyQt5 桌面版 (已冻结)
```

## 核心数据流

1. **Web 端**: 用户上传 → /api/upload → 返回 file_id → /api/score (SSE) → 后台线程运行 Scorer.score() → SSE 流式推送进度/结果
2. **CLI**: python -m vqa.cli score <target> --algo <name> → Scorer.score() → 打印/导出 JSON
3. **Scorer 调度**: 根据算法 spec 的 kind (FR/NR) + 输入类型 (image/video) → 调用对应的 image/video 函数
4. **进度回调**: progress_callback(current, total) → Web 端通过 SSE 推送 → 前端进度条 5%~95%

## 前端 UI 特性
- 街机 CRT 风格：星空背景、扫描线、像素字体 Press Start 2P
- 评级系统：S/A/B+/B/C/D 六档，评分翻滚动画
- 成就系统：首次评测/VSFA首战/评测老手/S级达人/全能选手等8项
- 逐帧曲线图：折线+渐变填色+均值参考线
- 键盘操作：Enter/Space/Esc 全流程控制
- KO 特效：评分结束时的动画效果
- SSE 进度流：实时进度条+三色渐变

## 依赖项
- numpy>=1.21, opencv-python-headless>=4.5
- flask, flask-cors, Pillow
- PyQt5 (GUI，已冻结)
- torch, torchvision, Pillow (VSFA 额外依赖，懒加载)

## 已知限制
- NIQE-Lite 在 JPEG 压缩失真上单调性反向（已知现象）
- VSFA 需要额外安装 PyTorch
- VSFA-V 仅支持视频，不支持单图
- Web 默认视频上限 60 帧，最大 200 帧
- PyQt5 GUI 已冻结不再维护

## 后续计划 (来自中期汇报)
- 第11-12周: 接入 VMAF (FFmpeg libvmaf)
- 第13-14周: 接入 VSFA 深度学习模型 (已完成)
- 第15周: TID2013/LIVE 基准测试 (SROCC/KROCC/PLCC/RMSE)
- 第16-17周: UI优化、答辩PPT
