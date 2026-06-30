# VQA Arcade Machine · 视觉质量评估街机评分台

> 图像 / 视频视觉质量评估 · Synthwave 街机风格交互 · 7 种算法 · Web / CLI 双通道

## 快速开始

```bash
# 安装依赖
pip install flask flask-cors numpy Pillow opencv-python-headless

# 启动 Web 版
python server.py
# → 浏览器打开 http://localhost:5100
```

> PyTorch 和模型权重（354 MB）为可选依赖，安装后解锁 VMAF / VSFA / VMAF-V / VSFA-V 四个深度学习算法。

## 7 种算法

| 算法 | 类别 | 模式 | 输入 | 输出 | 核心思路 |
|------|------|------|------|------|---------|
| **PSNR** | 传统 | FR 全参考 | 图/视频 | dB ↑ | 逐像素均方误差 |
| **SSIM** | 传统 | FR 全参考 | 图/视频 | 0~1 ↑ | 亮度/对比度/结构三通道对比 |
| **VMAF** | 深度学习 | FR 全参考 | 图 | 0~100 ↑ | ResNet50 双分支 Siamese 感知相似度 |
| **VMAF-V** | 深度学习 | FR 全参考 | 视频 | 0~100 ↑ | ResNet18 帧编码 + 时序平均池化 |
| **NIQE-Lite** | 传统 | NR 无参考 | 图/视频 | ~3~30 ↓ | 自然统计特征偏离分析（自实现轻量版） |
| **VSFA** | 深度学习 | NR 无参考 | 图 | DMOS ↓ | VGG16 + GAP 逐帧深度学习 |
| **VSFA-V** | 深度学习 | NR 无参考 | 视频 | MOS ↑ | VGG16 + 4 帧网络内时序聚合 |

### 优雅降级

Torch 采用懒加载机制：未安装 PyTorch 时 PSNR / SSIM / NIQE-Lite 正常工作，VMAF / VSFA 通路静默不可用，系统整体仍可运行。

## 特性

- 🎮 **Synthwave 街机 Web UI** — 霓虹网格地平线、CRT 扫描线、像素字体、日落光晕、glitch 转场
- 🤖 **4 个深度学习模型** — ResNet50 Siamese / ResNet18 时序池化 / VGG16 + GAP / VGG16 视频级聚合
- 📊 **SSE 实时进度** — 流式推送、三色渐变进度条、逐帧回调
- 🏆 **评级系统** — S/A/B+/B/C/D 六档，评分翻滚 + KO 特效
- 🎖️ **成就系统** — 9 项可解锁成就（深度学习先锋 / 视频大师 / 全能选手 / S 级达人等）
- 📈 **帧曲线图** — Canvas 折线 + 渐变填色 + 黄色虚线均值参考线
- 🔄 **FR / NR 双模式** — 全参考需原素材，无参考仅需待测文件
- ⌨️ **键盘操作** — Enter / Space / Esc 全流程控制 + 拖拽上传
- 📝 **使用说明面板** — 七算法卡片 + 操作步骤 + 快捷键速查

## 部署

### Cloudflare Tunnel（零成本公网上线）

```bash
# 安装 cloudflared & 启动
cloudflared tunnel --protocol http2 --url http://localhost:5100
# → 获得 *.trycloudflare.com HTTPS 公网地址
```

> ⚠️ 国内网络需加 `--protocol http2` 绕过 QUIC 封锁。

### Docker（长期稳定部署）

```bash
# 构建
docker compose build

# 启动（含 354MB 模型 + uploads 持久化 + 健康检查）
docker compose up -d

# 运维
./deploy.sh up|logs|restart|stop|status
```

> 详细部署指南见 [DEPLOY.md](./DEPLOY.md)，含腾讯云轻量服务器选购清单与域名 + Nginx + HTTPS 完整配置。

## 目录结构

```
server.py              Flask Web 后端
web/index.html         街机前端（单文件）
web/font/              像素字体 PressStart2P
vqa/cli.py             CLI 命令行入口
vqa/scorer.py          算法注册表 + 调度器
vqa/algos/             7 种算法实现 + 4 个 .pth 模型权重（354 MB）
vqa/gui/               PyQt5 桌面版（已冻结，不再维护）
samples/               测试样例素材
reports/demo_images/   答辩演示素材（AI 生成原图 + 失真版 + 视频）
scripts/               辅助脚本（报告生成 / PPT 生成 / 失真处理）
docs/report/           报告、PPT、试卷要求
```

## 演示素材

`reports/demo_images/pairs/` 包含答辩用的完整素材：

- **5 主题 × 3 档图像**（赛博城市 / 极光雪山 / 橘猫 / 甜点 / 蒸汽波日落，含原版 + 轻度 + 重度失真）
- **5 版本视频**（Synthwave 赛博城市短片，原版 + 模糊 + 帧压缩各两档）
- 全部素材已通过系统 API 实测打分，结果写入报告第五章

> 使用指南见 `reports/demo_images/演示素材使用指南.md`，含演示话术与实测分数。

## PyQt5 桌面版

原 PyQt5 桌面版仍在 `vqa/gui/` 中，但已冻结不再维护。启动：

```bash
pip install PyQt5
python -m vqa.gui
```

## GitHub

https://github.com/Kevin-XX/vqa-arcade
