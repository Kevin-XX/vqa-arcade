/**
 * 中期汇报 PPT 生成脚本
 * 主题：Midnight Executive 风格（深蓝主背景 + 冰蓝 + 青色高亮）
 * 字体：标题 Cambria Bold / 正文 Calibri
 *
 * 共 12 页：
 *  1. 封面
 *  2. 项目背景与目标
 *  3. 进度对照（开题→中期）
 *  4. 系统架构
 *  5. 算法实现 §1：FR (PSNR/SSIM)
 *  6. 算法实现 §2：NR (NIQE-Lite)
 *  7. GUI 设计与实现
 *  8. GUI 演示截图
 *  9. 实验结果（图像表 + 视频表）
 * 10. 关键技术：多线程不卡 UI
 * 11. VMAF 调研 & 后续路线
 * 12. 风险降级 & 致谢
 */
const pptxgen = require("pptxgenjs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const OUT = path.join(ROOT, "reports", "视觉质量评估_中期汇报.pptx");

// ============== 主题色 ==============
const C = {
  bgDark: "0B1220",      // 主深蓝背景
  bgPanel: "0F172A",     // 卡片底色
  bgLight: "F8FAFC",     // 浅色页背景
  navy: "1E2761",        // 标题深蓝
  ice: "CADCFC",         // 冰蓝高亮
  accent: "22D3EE",      // 青色高亮
  accent2: "60A5FA",     // 次高亮
  text: "E2E8F0",        // 浅色文本
  textDark: "1E293B",    // 深色文本
  muted: "94A3B8",       // 次要文本
  ok: "10B981",          // 绿
  warn: "F59E0B",        // 橙
  err: "F87171",         // 红
};

const FONT_T = "Cambria";
const FONT_B = "Calibri";

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 × 7.5
pres.author = "徐凯文 / 江子路 / 曹天诚 / 常家硕";
pres.title = "视觉质量评估应用 · 中期汇报";

const W = 13.333;
const H = 7.5;

// ============== 工具 ==============
function darkBg(slide) { slide.background = { color: C.bgDark }; }
function lightBg(slide) { slide.background = { color: C.bgLight }; }

function addPageNumber(slide, idx, total, dark = true) {
  slide.addText(`${idx} / ${total}`, {
    x: W - 1.2, y: H - 0.45, w: 1.0, h: 0.3,
    fontSize: 10, fontFace: FONT_B,
    color: dark ? C.muted : "94A3B8",
    align: "right",
    margin: 0,
  });
  slide.addText("VQA Studio · 中期汇报", {
    x: 0.5, y: H - 0.45, w: 6, h: 0.3,
    fontSize: 10, fontFace: FONT_B,
    color: dark ? C.muted : "94A3B8",
    align: "left",
    margin: 0,
  });
}

function pageHeader(slide, num, title, subtitle, dark = true) {
  // 左侧序号大字
  slide.addText(String(num).padStart(2, "0"), {
    x: 0.5, y: 0.35, w: 1.5, h: 1.1,
    fontSize: 60, fontFace: FONT_T, bold: true,
    color: dark ? C.accent : C.navy,
    align: "left", valign: "top",
    margin: 0,
  });
  // 标题
  slide.addText(title, {
    x: 1.7, y: 0.45, w: 10.5, h: 0.7,
    fontSize: 30, fontFace: FONT_T, bold: true,
    color: dark ? "FFFFFF" : C.navy,
    align: "left", valign: "middle",
    margin: 0,
  });
  // 副标题
  if (subtitle) {
    slide.addText(subtitle, {
      x: 1.7, y: 1.1, w: 11, h: 0.4,
      fontSize: 13, fontFace: FONT_B,
      color: dark ? C.muted : "64748B",
      align: "left", valign: "top",
      margin: 0,
    });
  }
  // 装饰条（细青色）
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 1.72, y: 1.55, w: 0.45, h: 0.05,
    fill: { color: C.accent }, line: { color: C.accent },
  });
}

function statCard(slide, x, y, w, h, big, label, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: C.bgPanel },
    line: { color: "1E293B", width: 1 },
  });
  // 顶边色条
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h: 0.05, fill: { color }, line: { color },
  });
  slide.addText(big, {
    x, y: y + 0.15, w, h: h * 0.55,
    fontSize: 36, fontFace: FONT_T, bold: true,
    color, align: "center", valign: "middle", margin: 0,
  });
  slide.addText(label, {
    x, y: y + h * 0.6, w, h: h * 0.35,
    fontSize: 11, fontFace: FONT_B,
    color: C.muted, align: "center", valign: "top", margin: 0,
  });
}

// ============== 1. 封面 ==============
{
  let s = pres.addSlide();
  darkBg(s);
  // 装饰渐变块（用半透明矩形堆叠模拟）
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.5, h: H,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 4.5, h: H,
    fill: { color: C.accent, transparency: 80 }, line: { color: C.accent, transparency: 100 },
  });
  // 大装饰圆
  s.addShape(pres.shapes.OVAL, {
    x: -1.5, y: H - 3, w: 3, h: 3,
    fill: { color: C.accent, transparency: 70 }, line: { color: C.accent, transparency: 100 },
  });
  s.addShape(pres.shapes.OVAL, {
    x: 3, y: -1.2, w: 2.4, h: 2.4,
    fill: { color: C.ice, transparency: 80 }, line: { color: C.ice, transparency: 100 },
  });

  // 左侧 课程信息
  s.addText("PROFESSIONAL DESIGN", {
    x: 0.5, y: 0.6, w: 4, h: 0.4,
    fontSize: 11, fontFace: FONT_B, bold: true, charSpacing: 4,
    color: C.accent, align: "left", margin: 0,
  });
  s.addText("专业综合设计 · 第 10 周", {
    x: 0.5, y: 1.0, w: 4, h: 0.4,
    fontSize: 13, fontFace: FONT_B,
    color: C.ice, align: "left", margin: 0,
  });

  // 右侧 主标题
  s.addText("视觉质量评估应用", {
    x: 5.0, y: 1.6, w: 8, h: 1.1,
    fontSize: 48, fontFace: FONT_T, bold: true,
    color: "FFFFFF", align: "left", margin: 0,
  });
  s.addText([
    { text: "VQA Studio", options: { color: C.accent, bold: true, fontFace: FONT_T } },
    { text: "  ·  ", options: { color: C.muted } },
    { text: "中期汇报", options: { color: C.ice, bold: true, fontFace: FONT_T } },
  ], {
    x: 5.0, y: 2.7, w: 8, h: 0.6,
    fontSize: 26, align: "left", margin: 0,
  });

  // 装饰横线
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.0, y: 3.5, w: 0.6, h: 0.05,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  // 一句话定位
  s.addText("图像 / 视频 · 全参考 + 无参考 · 多线程联调版本", {
    x: 5.0, y: 3.65, w: 8, h: 0.5,
    fontSize: 15, fontFace: FONT_B,
    color: C.ice, align: "left", margin: 0,
  });

  // 信息行
  s.addText([
    { text: "汇报组：", options: { color: C.muted, bold: true } },
    { text: "江子路 / 曹天诚 / 常家硕 / 徐凯文", options: { color: C.text } },
  ], {
    x: 5.0, y: 4.6, w: 8, h: 0.4,
    fontSize: 14, fontFace: FONT_B, align: "left", margin: 0,
  });
  s.addText([
    { text: "指导老师：", options: { color: C.muted, bold: true } },
    { text: "周飞", options: { color: C.text } },
  ], {
    x: 5.0, y: 5.0, w: 8, h: 0.4,
    fontSize: 14, fontFace: FONT_B, align: "left", margin: 0,
  });
  s.addText([
    { text: "汇报日期：", options: { color: C.muted, bold: true } },
    { text: "2026 年 5 月 19 日", options: { color: C.text } },
  ], {
    x: 5.0, y: 5.4, w: 8, h: 0.4,
    fontSize: 14, fontFace: FONT_B, align: "left", margin: 0,
  });

  // 底部小字
  s.addText("v0.1.0 · GUI 多线程联调 / VMAF 调研已完成", {
    x: 5.0, y: H - 0.7, w: 8, h: 0.3,
    fontSize: 10, fontFace: FONT_B,
    color: C.muted, align: "left", margin: 0,
  });
}

// ============== 2. 项目背景与目标 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 1, "项目背景与目标", "WHY WE BUILD VQA STUDIO");

  // 左：背景文字
  s.addText("背景", {
    x: 0.5, y: 1.85, w: 6, h: 0.4,
    fontSize: 16, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });
  s.addText([
    { text: "短视频 / 直播 / 视频会议 / 流媒体爆发", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "上下行带宽有限，编码 / 上采样 / 网络抖动均可能引入失真", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "需要一个可定量、可对比、可视化的工具", options: { bullet: true, color: C.text } },
  ], {
    x: 0.5, y: 2.3, w: 6.0, h: 2.3,
    fontSize: 14, fontFace: FONT_B,
    paraSpaceAfter: 6, margin: 4,
  });

  s.addText("目标", {
    x: 0.5, y: 4.6, w: 6, h: 0.4,
    fontSize: 16, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });
  s.addText([
    { text: "覆盖 FR (全参考) + NR (无参考) 两类算法", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "支持 图像 / 视频 双输入，逐帧得分曲线", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "PyQt5 GUI 多线程不卡顿，CLI 可批量自动化", options: { bullet: true, color: C.text } },
  ], {
    x: 0.5, y: 5.05, w: 6.0, h: 1.8,
    fontSize: 14, fontFace: FONT_B,
    paraSpaceAfter: 6, margin: 4,
  });

  // 右：四个统计卡
  statCard(s, 7.0, 1.85, 2.85, 1.5, "3", "已注册算法", C.accent);
  statCard(s, 9.95, 1.85, 2.85, 1.5, "6/6", "单元测试 PASS", C.ok);
  statCard(s, 7.0, 3.5, 2.85, 1.5, "0.23s", "30 帧视频 SSIM", C.accent2);
  statCard(s, 9.95, 3.5, 2.85, 1.5, "1200×760", "GUI 分辨率", C.ice);

  // 右下：算法标签
  const tagY = 5.15;
  const tags = [
    { t: "FR  PSNR", c: C.accent },
    { t: "FR  SSIM", c: C.accent },
    { t: "NR  NIQE-Lite", c: C.accent2 },
    { t: "FR  VMAF · 11-12 周", c: C.muted },
    { t: "NR  VSFA · 13-14 周", c: C.muted },
  ];
  let tx = 7.0;
  tags.forEach((tag) => {
    const w = 0.18 * tag.t.length + 0.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: tx, y: tagY, w, h: 0.42,
      fill: { color: C.bgPanel }, line: { color: tag.c, width: 1 },
      rectRadius: 0.06,
    });
    s.addText(tag.t, {
      x: tx, y: tagY, w, h: 0.42,
      fontSize: 11, fontFace: FONT_B, bold: true,
      color: tag.c, align: "center", valign: "middle", margin: 0,
    });
    tx += w + 0.12;
    if (tx > 12) { tx = 7.0; }
  });

  addPageNumber(s, 2, 12);
}

// ============== 3. 进度对照 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 2, "与开题计划的进度对照", "MILESTONE TRACKING");

  // 时间轴（横线）
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 3.5, w: 11.9, h: 0.04,
    fill: { color: "1E293B" }, line: { color: "1E293B" },
  });

  const milestones = [
    { x: 1.0,  label: "第 6-7 周",  task: "环境搭建 + CLI 跑通",       status: "done" },
    { x: 4.0,  label: "第 8-9 周",  task: "GUI 原型 + 模型加载",         status: "done" },
    { x: 7.0,  label: "第 10 周 ★",  task: "GUI 联调 / 多线程 / VMAF 调研", status: "now"  },
    { x: 10.0, label: "第 11-15 周", task: "VMAF / VSFA / 数据库验证",     status: "todo" },
    { x: 12.5, label: "第 16-17 周", task: "UI 优化 + 答辩",              status: "todo" },
  ];
  milestones.forEach((m) => {
    const color = m.status === "done" ? C.ok : m.status === "now" ? C.accent : C.muted;
    const r = 0.2;
    s.addShape(pres.shapes.OVAL, {
      x: m.x - r/2, y: 3.5 - r/2 + 0.02, w: r, h: r,
      fill: { color }, line: { color: "FFFFFF", width: 1 },
    });
    // 上方标签
    s.addText(m.label, {
      x: m.x - 1.2, y: 2.5, w: 2.4, h: 0.4,
      fontSize: 13, fontFace: FONT_T, bold: true, color,
      align: "center", margin: 0,
    });
    // 下方任务
    s.addText(m.task, {
      x: m.x - 1.4, y: 3.85, w: 2.8, h: 0.7,
      fontSize: 11, fontFace: FONT_B,
      color: m.status === "todo" ? C.muted : C.text,
      align: "center", valign: "top", margin: 0,
    });
  });

  // 当前节点 ★ 强调
  s.addText("中期汇报", {
    x: 5.6, y: 1.95, w: 2.8, h: 0.4,
    fontSize: 13, fontFace: FONT_T, bold: true, color: C.accent,
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.92, y: 2.4, w: 0.16, h: 1.0,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  // 底部三栏总结
  const cards = [
    { t: "已完成", c: C.ok, items: [
      "PSNR / SSIM / NIQE-Lite 全部上线",
      "PyQt5 GUI 4 区布局 + QSS 深色主题",
      "多线程不卡顿，6 单元测试通过",
    ]},
    { t: "本期里程碑", c: C.accent, items: [
      "算法挂到 GUI（拖拽 / 进度 / 曲线）",
      "QThread + 信号通路联调",
      "VMAF 集成路径调研报告完成",
    ]},
    { t: "下一阶段", c: C.muted, items: [
      "11-12 周：VMAF（FFmpeg + libvmaf）",
      "13-14 周：VSFA（PyTorch ResNet+GRU）",
      "15-17 周：TID2013/LIVE 验证 + 答辩",
    ]},
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 5.1, w: 4.0, h: 1.95,
      fill: { color: C.bgPanel }, line: { color: "1E293B" },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 5.1, w: 0.08, h: 1.95,
      fill: { color: c.c }, line: { color: c.c },
    });
    s.addText(c.t, {
      x: x + 0.2, y: 5.18, w: 3.8, h: 0.4,
      fontSize: 14, fontFace: FONT_T, bold: true,
      color: c.c, align: "left", margin: 0,
    });
    const items = c.items.map((t, j) => ({
      text: t, options: { bullet: true, breakLine: j !== c.items.length - 1, color: C.text },
    }));
    s.addText(items, {
      x: x + 0.2, y: 5.55, w: 3.7, h: 1.4,
      fontSize: 11, fontFace: FONT_B, paraSpaceAfter: 3, margin: 4,
    });
  });

  addPageNumber(s, 3, 12);
}

// ============== 4. 系统架构 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 3, "系统架构", "MODULE BREAKDOWN");

  // 三层结构（自上而下）
  const layerY = [1.95, 3.55, 5.55];
  const layers = [
    { y: 1.95, h: 1.2, title: "应用层", color: C.accent, mods: [
      { t: "CLI\nvqa.cli", x: 1.5 },
      { t: "GUI 主窗口\nMainWindow", x: 5.0 },
      { t: "GUI 离屏冒烟\nsmoke_test", x: 9.0 },
    ]},
    { y: 3.4, h: 1.6, title: "调度 / GUI 组件层", color: C.accent2, mods: [
      { t: "Scorer\n按算法+类型派发", x: 1.5 },
      { t: "ScoringWorker\n(QThread)", x: 5.0 },
      { t: "DropPreview\n拖拽预览", x: 9.0 },
      { t: "ScoreCurve\n逐帧曲线 (QPainter)", x: 11.5 },
    ]},
    { y: 5.3, h: 1.6, title: "算法 / IO 层", color: C.ice, mods: [
      { t: "PSNR", x: 1.0 },
      { t: "SSIM\n(11×11 高斯)", x: 3.0 },
      { t: "NIQE-Lite\n(MSCN+AGGD+锐+噪)", x: 5.0 },
      { t: "io_utils\n图像/视频/聚合", x: 8.0 },
      { t: "ALGORITHMS\n注册表", x: 11.0 },
    ]},
  ];

  layers.forEach((l) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: l.y, w: 12.3, h: l.h,
      fill: { color: C.bgPanel }, line: { color: "1E293B" },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y: l.y, w: 0.08, h: l.h,
      fill: { color: l.color }, line: { color: l.color },
    });
    s.addText(l.title, {
      x: 0.7, y: l.y + 0.05, w: 4, h: 0.4,
      fontSize: 13, fontFace: FONT_T, bold: true, color: l.color, margin: 0,
    });
    l.mods.forEach((m) => {
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: m.x, y: l.y + 0.5, w: 1.9, h: 1.0,
        fill: { color: C.bgDark }, line: { color: l.color, width: 1 },
        rectRadius: 0.08,
      });
      s.addText(m.t, {
        x: m.x, y: l.y + 0.5, w: 1.9, h: 1.0,
        fontSize: 11, fontFace: FONT_B, bold: true,
        color: C.text, align: "center", valign: "middle",
        paraSpaceAfter: 0, margin: 4,
      });
    });
  });

  // 中间连线（应用层 → 中间层 → 算法层）
  // 简单的箭头：竖线
  [3.15, 5.0].forEach((y) => {
    s.addShape(pres.shapes.LINE, {
      x: W / 2, y, w: 0, h: 0.25,
      line: { color: C.muted, width: 1, dashType: "dash" },
    });
  });

  addPageNumber(s, 4, 12);
}

// ============== 5. 算法实现 §1 - FR ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 4, "算法实现 ① ─ FR 全参考", "PSNR · SSIM");

  // 左：PSNR
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.85, w: 6.0, h: 5.0,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.85, w: 6.0, h: 0.05,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  s.addText("PSNR", {
    x: 0.7, y: 1.95, w: 5.6, h: 0.5,
    fontSize: 22, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
  });
  s.addText("Peak Signal-to-Noise Ratio · 越大越好 · dB", {
    x: 0.7, y: 2.45, w: 5.6, h: 0.4,
    fontSize: 12, fontFace: FONT_B, color: C.muted, margin: 0,
  });
  // 公式（用纯文本）
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.7, y: 2.95, w: 5.6, h: 0.95,
    fill: { color: C.bgDark }, line: { color: "1E293B" },
  });
  s.addText("PSNR = 10 · log₁₀ ( 1 / MSE )", {
    x: 0.7, y: 2.95, w: 5.6, h: 0.95,
    fontSize: 18, fontFace: "Consolas", bold: true,
    color: C.accent, align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "图像归一化到 [0,1] float32", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "MSE = 像素误差平方均值", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "自比 → ∞，工程实现取 100 dB 上限", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "对加性噪声敏感，对结构性失真不敏感", options: { bullet: true, color: C.warn } },
  ], {
    x: 0.7, y: 4.05, w: 5.6, h: 2.7,
    fontSize: 13, fontFace: FONT_B, paraSpaceAfter: 4, margin: 4,
  });

  // 右：SSIM
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.85, w: 6.0, h: 5.0,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.85, w: 6.0, h: 0.05,
    fill: { color: C.accent2 }, line: { color: C.accent2 },
  });
  s.addText("SSIM", {
    x: 7.05, y: 1.95, w: 5.6, h: 0.5,
    fontSize: 22, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
  });
  s.addText("Structural Similarity · 越大越好 · [0,1]", {
    x: 7.05, y: 2.45, w: 5.6, h: 0.4,
    fontSize: 12, fontFace: FONT_B, color: C.muted, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.05, y: 2.95, w: 5.6, h: 0.95,
    fill: { color: C.bgDark }, line: { color: "1E293B" },
  });
  s.addText("(2μxμy+C₁)(2σxy+C₂) / (μx²+μy²+C₁)(σx²+σy²+C₂)", {
    x: 7.05, y: 2.95, w: 5.6, h: 0.95,
    fontSize: 11, fontFace: "Consolas", bold: true,
    color: C.accent2, align: "center", valign: "middle", margin: 0,
  });
  s.addText([
    { text: "11×11 高斯窗滑动卷积（Wang 2004）", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "K₁=0.01, K₂=0.03，对应 C₁=2.55e-5", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "用 cv2.filter2D 替代纯 Python 循环", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "自比 = 1.0 ✓ ；模糊 / 噪声严格下降 ✓", options: { bullet: true, color: C.ok } },
  ], {
    x: 7.05, y: 4.05, w: 5.6, h: 2.7,
    fontSize: 13, fontFace: FONT_B, paraSpaceAfter: 4, margin: 4,
  });

  addPageNumber(s, 5, 12);
}

// ============== 6. 算法实现 §2 - NR ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 5, "算法实现 ② ─ NR 无参考", "NIQE-Lite (项目自实现)");

  // 大卡片：四特征
  s.addText("特征工程：四个互补维度", {
    x: 0.5, y: 1.9, w: 12, h: 0.4,
    fontSize: 16, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });

  const feats = [
    { num: "1", title: "MSCN 系数", desc: "全局方差 + 峰度，自然图像近高斯，失真越偏离越异常", color: C.accent },
    { num: "2", title: "MSCN 水平/垂直乘积", desc: "AGGD 拟合形状参数，敏感于噪声与模糊", color: C.accent2 },
    { num: "3", title: "拉普拉斯方差", desc: "图像锐度的经典度量，模糊越严重越接近 0", color: C.ice },
    { num: "4", title: "Immerkaer 噪声估计", desc: "单 5×5 拉普拉斯掩模卷积，抑制结构、保留噪声", color: C.warn },
  ];
  feats.forEach((f, i) => {
    const x = 0.5 + (i % 2) * 6.35;
    const y = 2.45 + Math.floor(i / 2) * 1.55;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 6.0, h: 1.4,
      fill: { color: C.bgPanel }, line: { color: "1E293B" },
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.2, y: y + 0.35, w: 0.7, h: 0.7,
      fill: { color: f.color }, line: { color: f.color },
    });
    s.addText(f.num, {
      x: x + 0.2, y: y + 0.35, w: 0.7, h: 0.7,
      fontSize: 22, fontFace: FONT_T, bold: true,
      color: C.bgDark, align: "center", valign: "middle", margin: 0,
    });
    s.addText(f.title, {
      x: x + 1.05, y: y + 0.25, w: 4.8, h: 0.45,
      fontSize: 16, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
    });
    s.addText(f.desc, {
      x: x + 1.05, y: y + 0.7, w: 4.8, h: 0.65,
      fontSize: 11, fontFace: FONT_B, color: C.text, margin: 0,
    });
  });

  // 底部：聚合公式 + 结论
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.7, w: 12.3, h: 1.2,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.7, w: 0.08, h: 1.2,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  s.addText("加权聚合", {
    x: 0.7, y: 5.78, w: 2.5, h: 0.4,
    fontSize: 14, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });
  s.addText("score = 0.4·MSCN_dev + 0.2·prod_kurt + 0.2·(1/sharp) + 0.2·noise   (越小越好)", {
    x: 0.7, y: 6.18, w: 12, h: 0.45,
    fontSize: 13, fontFace: "Consolas", color: C.text, margin: 0,
  });
  s.addText("✓ 纯 NumPy / OpenCV，跨平台无依赖；✗ 量纲与官方 NIQE 不一致 → 后期由 VSFA 替换", {
    x: 0.7, y: 6.45, w: 12, h: 0.4,
    fontSize: 11, fontFace: FONT_B, color: C.muted, margin: 0,
  });

  addPageNumber(s, 6, 12);
}

// ============== 7. GUI 设计与实现 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 6, "GUI 设计与实现", "PyQt5 · 4 区布局 · 深色 QSS");

  const zones = [
    { n: "①", title: "输入区", desc: "拖拽 / 点击 · 图片直接显示 · 视频显示首帧", color: C.accent },
    { n: "②", title: "控制区", desc: "FR/NR 切换 · 算法下拉 · stride · max-frames", color: C.accent2 },
    { n: "③", title: "展示区", desc: "进度条 + 实时日志 + 逐帧得分曲线 (QPainter)", color: C.ice },
    { n: "④", title: "结果区", desc: "大字号 MOS · 聚合统计 · 一键导出 JSON", color: C.ok },
  ];
  // 左侧：四区描述
  zones.forEach((z, i) => {
    const y = 1.95 + i * 1.2;
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: y + 0.05, w: 0.7, h: 0.7,
      fill: { color: z.color }, line: { color: z.color },
    });
    s.addText(z.n, {
      x: 0.6, y: y + 0.05, w: 0.7, h: 0.7,
      fontSize: 22, fontFace: FONT_T, bold: true,
      color: C.bgDark, align: "center", valign: "middle", margin: 0,
    });
    s.addText(z.title, {
      x: 1.45, y: y, w: 4.8, h: 0.45,
      fontSize: 17, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
    });
    s.addText(z.desc, {
      x: 1.45, y: y + 0.45, w: 5.5, h: 0.5,
      fontSize: 11, fontFace: FONT_B, color: C.muted, margin: 0,
    });
  });

  // 右侧：截图（启动空白态）
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.2, y: 1.85, w: 5.7, h: 4.3,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addImage({
    path: path.join(ROOT, "reports", "demo_frames", "01_startup.png"),
    x: 7.32, y: 1.95, w: 5.46, h: 4.1,
    sizing: { type: "contain", w: 5.46, h: 4.1 },
  });
  s.addText("MainWindow 1200×760 启动态", {
    x: 7.2, y: 6.25, w: 5.7, h: 0.35,
    fontSize: 11, fontFace: FONT_B, color: C.muted,
    align: "center", margin: 0,
  });

  // 底部技术栈
  s.addText("PyQt5 · QObject + QThread · pyqtSignal · QSS 自定义深色主题 · QPainter 自绘曲线", {
    x: 0.5, y: 6.9, w: 12.3, h: 0.4,
    fontSize: 12, fontFace: FONT_B, color: C.accent,
    align: "center", margin: 0,
  });

  addPageNumber(s, 7, 12);
}

// ============== 8. GUI 演示截图 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 7, "GUI 演示走查", "样例：dis_blur.mp4 vs ref.mp4 · SSIM · stride=1");

  // 4 张截图水平摆 + 标签
  const shots = [
    { f: "02_loaded.png",        label: "① 双视频加载" },
    { f: "03_algo_selected.png", label: "② SSIM 已选中" },
    { f: "07_running.png",       label: "③ 评估中（曲线渐显）" },
    { f: "10_final.png",         label: "④ 完成 SSIM=0.7301" },
  ];
  const W_S = 2.95, H_S = 2.0, GAP = 0.1, X0 = 0.5, Y0 = 2.0;
  shots.forEach((sh, i) => {
    const x = X0 + i * (W_S + GAP);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: Y0, w: W_S, h: H_S + 0.5,
      fill: { color: C.bgPanel }, line: { color: "1E293B" },
    });
    s.addImage({
      path: path.join(ROOT, "reports", "demo_frames", sh.f),
      x: x + 0.05, y: Y0 + 0.05, w: W_S - 0.1, h: H_S,
      sizing: { type: "contain", w: W_S - 0.1, h: H_S },
    });
    s.addText(sh.label, {
      x, y: Y0 + H_S + 0.1, w: W_S, h: 0.35,
      fontSize: 11, fontFace: FONT_B, bold: true,
      color: C.ice, align: "center", margin: 0,
    });
  });

  // 下方：分数大字 + 解读
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.0, w: 12.3, h: 2.05,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.0, w: 0.08, h: 2.05,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  // 大数字
  s.addText("0.7301", {
    x: 0.7, y: 5.05, w: 3.5, h: 1.0,
    fontSize: 64, fontFace: FONT_T, bold: true,
    color: C.accent, align: "center", valign: "middle", margin: 0,
  });
  s.addText("SSIM 视频均值", {
    x: 0.7, y: 5.95, w: 3.5, h: 0.35,
    fontSize: 12, fontFace: FONT_B,
    color: C.muted, align: "center", margin: 0,
  });
  s.addText("逐帧 N=25 · σ=0.0090 · min=0.7237 · max=0.7578", {
    x: 0.7, y: 6.30, w: 3.5, h: 0.5,
    fontSize: 11, fontFace: FONT_B,
    color: C.text, align: "center", margin: 0,
  });

  // 右侧解读
  s.addText([
    { text: "✅ 评估期间窗口可拖动 / 滚动，主线程零冻结", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "✅ 进度条 busy 状态 + 日志区实时刷新", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "✅ 曲线区 25 个数据点逐帧绘出，平滑连贯", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "✅ 离屏冒烟测试 (smoke_test) 与 CLI 输出完全一致", options: { bullet: true, color: C.ok } },
  ], {
    x: 4.5, y: 5.1, w: 8.2, h: 1.85,
    fontSize: 13, fontFace: FONT_B, paraSpaceAfter: 4, margin: 6,
  });

  addPageNumber(s, 8, 12);
}

// ============== 9. 实验结果 ==============
{
  let s = pres.addSlide(); lightBg(s);
  pageHeader(s, 8, "实验结果", "BENCHMARK · 单调性验证", false);

  // 图像表
  s.addText("图像（参考 ref.png）", {
    x: 0.5, y: 1.85, w: 6, h: 0.4,
    fontSize: 14, fontFace: FONT_T, bold: true, color: C.navy, margin: 0,
  });

  const imgRows = [
    [
      { text: "失真类型", options: { bold: true, color: "FFFFFF", fill: { color: C.navy } } },
      { text: "PSNR ↑", options: { bold: true, color: "FFFFFF", fill: { color: C.navy }, align: "right" } },
      { text: "SSIM ↑", options: { bold: true, color: "FFFFFF", fill: { color: C.navy }, align: "right" } },
      { text: "NIQE-Lite ↓", options: { bold: true, color: "FFFFFF", fill: { color: C.navy }, align: "right" } },
    ],
    [{ text: "原图（自比）" }, { text: "100.000 dB", options: { align: "right" } }, { text: "1.0000", options: { align: "right" } }, { text: "3.656", options: { align: "right" } }],
    [{ text: "高斯模糊 σ=4" }, { text: "25.534 dB", options: { align: "right" } }, { text: "0.6870", options: { align: "right" } }, { text: "6.612", options: { align: "right", bold: true, color: "B85042" } }],
    [{ text: "高斯噪声 σ=25/255" }, { text: "24.020 dB", options: { align: "right" } }, { text: "0.4874", options: { align: "right", bold: true, color: "B85042" } }, { text: "6.358", options: { align: "right" } }],
    [{ text: "JPEG q=12" }, { text: "29.382 dB", options: { align: "right" } }, { text: "0.7426", options: { align: "right" } }, { text: "3.376", options: { align: "right", color: "F59E0B" } }],
  ];
  s.addTable(imgRows, {
    x: 0.5, y: 2.3, w: 6.3,
    colW: [2.4, 1.3, 1.3, 1.3],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", color: "E2E8F0", pt: 0.5 },
    color: C.textDark,
    rowH: 0.42,
  });

  // 视频表
  s.addText("视频（参考 ref.mp4，前 30 帧）", {
    x: 7.0, y: 1.85, w: 6, h: 0.4,
    fontSize: 14, fontFace: FONT_T, bold: true, color: C.navy, margin: 0,
  });
  const vidRows = [
    [
      { text: "失真类型", options: { bold: true, color: "FFFFFF", fill: { color: C.navy } } },
      { text: "PSNR ↑", options: { bold: true, color: "FFFFFF", fill: { color: C.navy }, align: "right" } },
      { text: "SSIM ↑", options: { bold: true, color: "FFFFFF", fill: { color: C.navy }, align: "right" } },
      { text: "NIQE-Lite ↓", options: { bold: true, color: "FFFFFF", fill: { color: C.navy }, align: "right" } },
    ],
    [{ text: "原视频" }, { text: "100.000 dB", options: { align: "right" } }, { text: "1.0000", options: { align: "right" } }, { text: "3.557", options: { align: "right" } }],
    [{ text: "视频 模糊" }, { text: "27.194 dB", options: { align: "right" } }, { text: "0.7329", options: { align: "right" } }, { text: "4.575", options: { align: "right", bold: true, color: "B85042" } }],
    [{ text: "视频 噪声" }, { text: "27.564 dB", options: { align: "right" } }, { text: "0.6448", options: { align: "right", bold: true, color: "B85042" } }, { text: "4.562", options: { align: "right" } }],
  ];
  s.addTable(vidRows, {
    x: 7.0, y: 2.3, w: 5.8,
    colW: [2.0, 1.3, 1.3, 1.2],
    fontSize: 11, fontFace: FONT_B,
    border: { type: "solid", color: "E2E8F0", pt: 0.5 },
    color: C.textDark,
    rowH: 0.42,
  });

  // 底部：观察结论
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.85, w: 12.3, h: 2.15,
    fill: { color: "FFFFFF" }, line: { color: "E2E8F0" },
  });
  s.addText("观察结论", {
    x: 0.7, y: 4.95, w: 5, h: 0.4,
    fontSize: 14, fontFace: FONT_T, bold: true, color: C.navy, margin: 0,
  });
  s.addText([
    { text: "PSNR / SSIM 在所有失真上严格低于无失真 → 基本单调性正确 ✓", options: { bullet: true, breakLine: true, color: C.textDark } },
    { text: "NIQE-Lite 在模糊 / 噪声上得分明显升高（3.66 → 6.61 / 6.36），无参考通路可用 ✓", options: { bullet: true, breakLine: true, color: C.textDark } },
    { text: "JPEG q=12 出现「高频被抹平 → NIQE 反而下降」（已知局限，将由官方 NIQE / VSFA 替换）", options: { bullet: true, breakLine: true, color: "92400E" } },
    { text: "性能：单图 PSNR/SSIM < 20 ms；30 帧视频 SSIM ≈ 0.23s，GUI 全程流畅", options: { bullet: true, color: C.textDark } },
  ], {
    x: 0.7, y: 5.4, w: 12, h: 1.55,
    fontSize: 12, fontFace: FONT_B, paraSpaceAfter: 4, margin: 4,
  });

  addPageNumber(s, 9, 12, false);
}

// ============== 10. 关键技术：多线程不卡 UI ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 9, "关键技术 · 多线程不卡 UI", "QObject + QThread + pyqtSignal");

  // 左：流程图
  s.addText("信号通路", {
    x: 0.5, y: 1.85, w: 6, h: 0.4,
    fontSize: 16, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });

  // 三个块：UI / Thread / Worker
  const flow = [
    { x: 0.5, y: 2.4, w: 2.4, label: "MainWindow\n(UI 主线程)", color: C.accent },
    { x: 3.2, y: 2.4, w: 2.4, label: "QThread", color: C.accent2 },
    { x: 5.9, y: 2.4, w: 2.4, label: "ScoringWorker\n(QObject)", color: C.ice },
  ];
  flow.forEach((f) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: f.x, y: f.y, w: f.w, h: 1.0,
      fill: { color: C.bgPanel }, line: { color: f.color, width: 2 },
      rectRadius: 0.1,
    });
    s.addText(f.label, {
      x: f.x, y: f.y, w: f.w, h: 1.0,
      fontSize: 12, fontFace: FONT_B, bold: true,
      color: f.color, align: "center", valign: "middle", margin: 4,
    });
  });
  // 箭头
  [
    { x: 2.9, y: 2.85, w: 0.3, h: 0 },
    { x: 5.6, y: 2.85, w: 0.3, h: 0 },
  ].forEach((a) => {
    s.addShape(pres.shapes.LINE, {
      x: a.x, y: a.y, w: a.w, h: 0,
      line: { color: C.muted, width: 1.5, endArrowType: "triangle" },
    });
  });

  // 信号回流（虚线 + 标签）
  s.addText("← progress / log / finished / failed (pyqtSignal)", {
    x: 0.5, y: 3.55, w: 7.8, h: 0.4,
    fontSize: 11, fontFace: FONT_B, color: C.warn,
    align: "center", margin: 0,
  });
  s.addShape(pres.shapes.LINE, {
    x: 7.1, y: 3.5, w: -6.0, h: 0,
    line: { color: C.warn, width: 1, dashType: "dash", endArrowType: "triangle" },
  });

  // 关键代码片段
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.1, w: 7.8, h: 2.85,
    fill: { color: C.bgDark }, line: { color: "1E293B" },
  });
  s.addText("关键代码（节选）", {
    x: 0.7, y: 4.18, w: 7.6, h: 0.35,
    fontSize: 12, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });
  const code =
`self._thread = QtCore.QThread()
self._worker = ScoringWorker(algo, target, ref, stride, max_frames)
self._worker.moveToThread(self._thread)

self._thread.started.connect(self._worker.run)
self._worker.log.connect(self._log)         # 日志回主线程
self._worker.finished.connect(self._on_finished)  # 完成回 UI
self._worker.failed.connect(self._on_failed)
self._worker.finished.connect(self._thread.quit)  # 自动退出线程

self._thread.start()`;
  s.addText(code, {
    x: 0.7, y: 4.55, w: 7.6, h: 2.3,
    fontSize: 11, fontFace: "Consolas", color: C.text,
    align: "left", valign: "top", margin: 6,
  });

  // 右：效果对比
  s.addText("收益验证", {
    x: 8.6, y: 1.85, w: 4.2, h: 0.4,
    fontSize: 16, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });
  const wins = [
    { stat: "0", unit: "次主线程冻结", color: C.ok },
    { stat: "100%", unit: "信号通路与 CLI 一致", color: C.ok },
    { stat: "25", unit: "帧曲线逐帧渲染", color: C.accent },
    { stat: "可拖动", unit: "评估中窗口仍响应", color: C.accent2 },
  ];
  wins.forEach((w, i) => {
    const y = 2.4 + i * 1.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 8.6, y, w: 4.2, h: 1.0,
      fill: { color: C.bgPanel }, line: { color: "1E293B" },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 8.6, y, w: 0.08, h: 1.0,
      fill: { color: w.color }, line: { color: w.color },
    });
    s.addText(w.stat, {
      x: 8.7, y: y + 0.05, w: 1.6, h: 0.9,
      fontSize: 30, fontFace: FONT_T, bold: true,
      color: w.color, align: "center", valign: "middle", margin: 0,
    });
    s.addText(w.unit, {
      x: 10.4, y: y + 0.05, w: 2.3, h: 0.9,
      fontSize: 12, fontFace: FONT_B,
      color: C.text, align: "left", valign: "middle", margin: 4,
    });
  });

  addPageNumber(s, 10, 12);
}

// ============== 11. VMAF 调研 + 路线 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 10, "VMAF 调研 与 后续路线", "11-12 周交付计划");

  // 左：VMAF 调研要点
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.85, w: 6.0, h: 5.1,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 1.85, w: 6.0, h: 0.05,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  s.addText("VMAF 调研要点", {
    x: 0.7, y: 1.95, w: 5.6, h: 0.45,
    fontSize: 18, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
  });
  s.addText("Video Multi-Method Assessment Fusion · Netflix 2016", {
    x: 0.7, y: 2.45, w: 5.6, h: 0.35,
    fontSize: 11, fontFace: FONT_B, color: C.muted, margin: 0,
  });

  s.addText([
    { text: "VIF (4 尺度) + DLM 细节损失 + TI 时域信息 → SVR 回归", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "默认模型 vmaf_v0.6.1（1080p）；SDR / HDR 分别专用模型", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "Python 包 vmaf-python 老旧 → 选择 ffmpeg + libvmaf 子进程", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "ffmpeg -lavfi libvmaf 流式输出 JSON，可逐帧解析", options: { bullet: true, breakLine: true, color: C.text } },
    { text: "GUI 已用 QThread + 信号通路，新增 vqa/algos/vmaf.py 即可挂载", options: { bullet: true, color: C.ok } },
  ], {
    x: 0.7, y: 2.85, w: 5.6, h: 4.0,
    fontSize: 12, fontFace: FONT_B, paraSpaceAfter: 6, margin: 6,
  });

  // 右：阶段路线表
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.85, w: 6.0, h: 5.1,
    fill: { color: C.bgPanel }, line: { color: "1E293B" },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.85, y: 1.85, w: 6.0, h: 0.05,
    fill: { color: C.accent2 }, line: { color: C.accent2 },
  });
  s.addText("阶段路线", {
    x: 7.05, y: 1.95, w: 5.6, h: 0.45,
    fontSize: 18, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
  });

  const stages = [
    { week: "11-12", task: "接入 VMAF (FFmpeg + libvmaf)", out: "vqa/algos/vmaf.py + GUI 算法菜单" },
    { week: "13-14", task: "接入 VSFA (PyTorch + ResNet+GRU)", out: "权重加载 + 单视频推理" },
    { week: "15",    task: "TID2013 / LIVE 数据库验证",          out: "SROCC / KROCC / PLCC / RMSE 表" },
    { week: "16-17", task: "UI 优化 + 答辩 PPT + 论文",          out: "终验交付包" },
  ];
  stages.forEach((st, i) => {
    const y = 2.6 + i * 1.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 7.05, y: y + 0.12, w: 1.0, h: 0.6,
      fill: { color: C.accent }, line: { color: C.accent },
      rectRadius: 0.06,
    });
    s.addText(`W${st.week}`, {
      x: 7.05, y: y + 0.12, w: 1.0, h: 0.6,
      fontSize: 13, fontFace: FONT_T, bold: true,
      color: C.bgDark, align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.task, {
      x: 8.2, y: y + 0.05, w: 4.5, h: 0.45,
      fontSize: 13, fontFace: FONT_T, bold: true, color: "FFFFFF", margin: 0,
    });
    s.addText("→ " + st.out, {
      x: 8.2, y: y + 0.5, w: 4.5, h: 0.4,
      fontSize: 10, fontFace: FONT_B, color: C.muted, margin: 0,
    });
  });

  addPageNumber(s, 11, 12);
}

// ============== 12. 风险 & 致谢 ==============
{
  let s = pres.addSlide(); darkBg(s);
  pageHeader(s, 11, "风险降级 与 致谢", "RISK MITIGATION & THANKS");

  // 风险表格
  s.addText("风险与降级方案", {
    x: 0.5, y: 1.85, w: 6, h: 0.4,
    fontSize: 16, fontFace: FONT_T, bold: true, color: C.accent, margin: 0,
  });

  const risks = [
    { r: "VMAF 在 macOS 编译失败", c: "libvmaf 依赖 meson/ninja",     m: "用 Netflix 静态二进制 / Docker 内运行", lvl: C.warn },
    { r: "VSFA 推理过慢导致 UI 阻塞", c: "单视频 > 5s 推理",         m: "已 QThread；进一步分块推理 + 流式回吐", lvl: C.accent },
    { r: "NIQE-Lite 在 JPEG 单调性反向", c: "高频抹平 → NIQE 下降", m: "由官方 NIQE / VSFA 替换，不影响中期演示", lvl: C.muted },
  ];

  risks.forEach((rk, i) => {
    const y = 2.4 + i * 1.15;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 12.3, h: 1.0,
      fill: { color: C.bgPanel }, line: { color: "1E293B" },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 0.08, h: 1.0,
      fill: { color: rk.lvl }, line: { color: rk.lvl },
    });
    s.addText(rk.r, {
      x: 0.7, y: y + 0.1, w: 4.3, h: 0.8,
      fontSize: 13, fontFace: FONT_T, bold: true,
      color: "FFFFFF", valign: "middle", margin: 4,
    });
    s.addText(rk.c, {
      x: 5.0, y: y + 0.1, w: 3.0, h: 0.8,
      fontSize: 11, fontFace: FONT_B,
      color: C.muted, valign: "middle", margin: 4,
    });
    s.addText("→ " + rk.m, {
      x: 8.1, y: y + 0.1, w: 4.6, h: 0.8,
      fontSize: 12, fontFace: FONT_B,
      color: C.text, valign: "middle", margin: 4,
    });
  });

  // 致谢条
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.95, w: 12.3, h: 1.0,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  s.addText("感谢周飞老师的指导，感谢小组成员的协作。期待中期反馈！", {
    x: 0.5, y: 5.95, w: 8.5, h: 1.0,
    fontSize: 16, fontFace: FONT_T, bold: true,
    color: "FFFFFF", align: "left", valign: "middle", margin: 16,
  });
  s.addText("THANK YOU", {
    x: 9.5, y: 5.95, w: 3.3, h: 1.0,
    fontSize: 22, fontFace: FONT_T, bold: true, charSpacing: 6,
    color: C.accent, align: "center", valign: "middle", margin: 0,
  });

  addPageNumber(s, 12, 12);
}

// ============== 输出 ==============
pres.writeFile({ fileName: OUT }).then((p) => {
  console.log("PPT 已生成：" + p);
});
