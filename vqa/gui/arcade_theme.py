"""街机主题系统：统一配色、字体、样式常量，全局 QSS 工厂。"""
from __future__ import annotations
import os
from PyQt5 import QtGui, QtWidgets, QtCore

# ── 注册像素字体（懒加载，需 QApplication 已存在）──
_FONT_PATH = os.path.join(os.path.dirname(__file__), "PressStart2P.ttf")
_PIXEL_FONT_ID = None
_PIXEL_FAMILY = None

def _ensure_pixel_font():
    global _PIXEL_FONT_ID, _PIXEL_FAMILY
    if _PIXEL_FONT_ID is not None:
        return
    if not os.path.exists(_FONT_PATH):
        _PIXEL_FONT_ID = -2
        return
    try:
        app = QtWidgets.QApplication.instance()
        if app is None:
            _PIXEL_FONT_ID = -2
            return
        _PIXEL_FONT_ID = QtGui.QFontDatabase.addApplicationFont(_FONT_PATH)
        if _PIXEL_FONT_ID >= 0:
            families = QtGui.QFontDatabase.applicationFontFamilies(_PIXEL_FONT_ID)
            _PIXEL_FAMILY = families[0] if families else None
        else:
            _PIXEL_FAMILY = None
    except Exception:
        _PIXEL_FONT_ID = -2

def pixel_font(size: int) -> QtGui.QFont:
    _ensure_pixel_font()
    if _PIXEL_FAMILY:
        return QtGui.QFont(_PIXEL_FAMILY, size)
    return QtGui.QFont("SF Mono, Menlo, Courier New", size)

def neon_glow(widget: QtWidgets.QWidget, color: str, radius: int = 18):
    """给 widget 添加霓虹发光效果。"""
    eff = QtWidgets.QGraphicsDropShadowEffect()
    eff.setBlurRadius(radius)
    eff.setColor(QtGui.QColor(color))
    eff.setOffset(0, 0)
    widget.setGraphicsEffect(eff)
    return eff

# ── 核心配色 ──
C_BG      = "#0a0a1a"    # 极暗蓝黑背景
C_BG_DARK = "#050510"    # 更深背景（弹窗/卡片）
C_NEON_BLUE  = "#00f0ff"
C_NEON_PINK  = "#ff2d95"
C_GREEN_OK   = "#0fff50"
C_YELLOW     = "#ffe600"
C_PURPLE     = "#a78bfa"
C_RED_ERR    = "#f87171"
C_DIM        = "#334155"    # 禁用/暗块
C_MUTED      = "#64748b"    # 次级文案
C_WHITE      = "#e2e8f0"

# ── 颜色注册表（QSS 可用变量名）─
COLORS = {
    "bg":      C_BG,
    "bg_dark": C_BG_DARK,
    "neon":    C_NEON_BLUE,
    "pink":    C_NEON_PINK,
    "green":   C_GREEN_OK,
    "yellow":  C_YELLOW,
    "purple":  C_PURPLE,
    "red":     C_RED_ERR,
    "dim":     C_DIM,
    "muted":   C_MUTED,
    "white":   C_WHITE,
}

# ── 字体 ──
FONT_MONO = "SF Mono, Menlo, monospace"
FONT_DISPLAY = "Helvetica, Arial, sans-serif"
FONT_SCORE = "SF Mono, Menlo, Courier New, monospace"
FONT_CN = "PingFang SC, Helvetica, sans-serif"

def mono_font(size: int, bold: bool = False) -> QtGui.QFont:
    f = QtGui.QFont(FONT_MONO, size)
    f.setBold(bold)
    return f

def cn_font(size: int, bold: bool = False) -> QtGui.QFont:
    f = QtGui.QFont(FONT_CN, size)
    f.setBold(bold)
    return f

# ── 全局 QSS ──
GLOBAL_QSS = f"""
QMainWindow, QWidget#page {{
    background: {C_BG};
    color: {C_WHITE};
}}
QLabel {{ color: {C_WHITE}; }}
QComboBox, QSpinBox {{
    background: {C_BG_DARK};
    color: {C_WHITE};
    padding: 4px 8px;
    border: 1px solid {C_DIM};
    border-radius: 4px;
    min-height: 20px;
}}
QPushButton#start_btn {{
    background: transparent;
    color: {C_GREEN_OK};
    border: 2px solid {C_GREEN_OK};
    padding: 12px 32px;
    font-size: 18px;
    font-weight: bold;
    border-radius: 4px;
}}
QPushButton#start_btn:hover {{
    background: {C_GREEN_OK};
    color: {C_BG};
}}
QPushButton#action_btn {{
    background: transparent;
    color: {C_NEON_BLUE};
    border: 1px solid {C_NEON_BLUE};
    padding: 8px 20px;
    font-size: 14px;
    border-radius: 4px;
}}
QPushButton#action_btn:hover {{
    background: {C_NEON_BLUE};
    color: {C_BG};
}}
QPushButton#danger_btn {{
    background: transparent;
    color: {C_NEON_PINK};
    border: 1px solid {C_NEON_PINK};
    padding: 8px 20px;
    font-size: 14px;
    border-radius: 4px;
}}
QPushButton#danger_btn:hover {{
    background: {C_NEON_PINK};
    color: {C_BG};
}}
"""

# ── 评级系统 ──
def compute_rank(score: float, algo: str) -> tuple[str, str]:
    """根据分数和算法类型返回 (评级, 颜色)。"""
    higher_better = algo in {"PSNR", "SSIM"}
    if higher_better:
        if score >= 0.95:   return "S",  C_GREEN_OK
        elif score >= 0.85: return "A",  C_NEON_BLUE
        elif score >= 0.70: return "B+", C_YELLOW
        elif score >= 0.50: return "B",  C_YELLOW
        elif score >= 0.30: return "C",  C_NEON_PINK
        else:               return "D",  C_RED_ERR
    else:
        # PSNR 例外：越大越好
        if algo == "PSNR":
            if score >= 45:     return "S",  C_GREEN_OK
            elif score >= 35:   return "A",  C_NEON_BLUE
            elif score >= 25:   return "B+", C_YELLOW
            elif score >= 18:   return "B",  C_YELLOW
            else:               return "C",  C_NEON_PINK
        # NIQE / VSFA：越小越好
        if score <= 10:     return "S",  C_GREEN_OK
        elif score <= 25:   return "A",  C_NEON_BLUE
        elif score <= 40:   return "B+", C_YELLOW
        elif score <= 55:   return "B",  C_YELLOW
        elif score <= 70:   return "C",  C_NEON_PINK
        else:               return "D",  C_RED_ERR
