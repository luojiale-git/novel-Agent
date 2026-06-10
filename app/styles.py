"""
天机 GUI 全局样式表 — 专业深色创作主题 v2
=========================================
设计系统：
  - 色彩: 品牌蓝 #6C8EBF | 强调金 #D4A84B | 成功绿 #4CAF7C | 危险红 #E05252
  - 字体比例尺: 24/18/15/13/12/11 px
  - 间距栅格: 4px 基准 → 4/8/12/16/20/24/32
  - 圆角: 小 4px | 中 6px | 大 8px | 圆 50%
"""


# ============================================================
# 色彩变量 (集中定义，方便后续提取为 QSS 变量)
# ============================================================
class Color:
    # 品牌
    PRIMARY = "#6C8EBF"
    PRIMARY_HOVER = "#8BAAD5"
    PRIMARY_PRESSED = "#5679A8"
    ACCENT_GOLD = "#D4A84B"
    ACCENT_GOLD_HOVER = "#E0BA6A"

    # 语义
    SUCCESS = "#4CAF7C"
    SUCCESS_HOVER = "#66C795"
    DANGER = "#E05252"
    DANGER_HOVER = "#E87373"
    WARNING = "#E8A84B"

    # 表面
    SURFACE_0 = "#18191C"  # 最深背景 (主窗口)
    SURFACE_1 = "#1E1F23"  # 标准背景 (面板)
    SURFACE_2 = "#25262B"  # 略高一层 (列表/卡片)
    SURFACE_3 = "#2D2E33"  # 导航栏/标题栏
    SURFACE_4 = "#36373D"  # 按钮/输入框背景

    # 边框
    BORDER = "#323339"
    BORDER_LIGHT = "#3D3E44"
    BORDER_FOCUS = "#6C8EBF"

    # 文字
    TEXT_PRIMARY = "#E4E4E7"
    TEXT_SECONDARY = "#9CA3AF"
    TEXT_MUTED = "#6B7280"
    TEXT_PLACEHOLDER = "#5C5F6A"

    # 特殊
    SELECTION_BG = "#2E446A"  # 选中背景
    SCROLLBAR_HANDLE = "#4A4D55"
    SCROLLBAR_HOVER = "#5E626C"
    TRANSPARENT = "transparent"


# ============================================================
# 全局样式表
# ============================================================
APP_STYLE = f"""
/* =================================================================
   全局基础
   ================================================================= */
QWidget {{
    font-family: "Microsoft YaHei UI", "PingFang SC", "Segoe UI", "Noto Sans SC", sans-serif;
    font-size: 13px;
    color: {Color.TEXT_PRIMARY};
    background-color: {Color.SURFACE_0};
}}

/* =================================================================
   主窗口
   ================================================================= */
QMainWindow {{
    background-color: {Color.SURFACE_0};
}}

/* =================================================================
   菜单栏
   ================================================================= */
QMenuBar {{
    background-color: {Color.SURFACE_3};
    border-bottom: 1px solid {Color.BORDER};
    padding: 2px 0;
    font-size: 13px;
}}
QMenuBar::item {{
    padding: 4px 14px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: {Color.SURFACE_4};
}}
QMenu {{
    background-color: {Color.SURFACE_2};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 28px 6px 16px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {Color.SELECTION_BG};
    color: {Color.TEXT_PRIMARY};
}}
QMenu::separator {{
    height: 1px;
    background: {Color.BORDER};
    margin: 4px 8px;
}}

/* =================================================================
   状态栏
   ================================================================= */
QStatusBar {{
    background-color: {Color.SURFACE_3};
    border-top: 1px solid {Color.BORDER};
    color: {Color.TEXT_MUTED};
    font-size: 12px;
    padding: 2px 12px;
}}

/* =================================================================
   信息栏 (NovelPanel 顶部)
   ================================================================= */
QLabel.info-bar {{
    background-color: {Color.SURFACE_3};
    border-bottom: 1px solid {Color.BORDER};
    padding: 10px 20px;
    font-size: 13px;
    color: {Color.TEXT_SECONDARY};
}}

/* =================================================================
   侧栏故事列表
   ================================================================= */
QListWidget {{
    background-color: {Color.SURFACE_1};
    border: none;
    border-right: 1px solid {Color.BORDER};
    outline: none;
    padding: 4px;
    font-size: 13px;
}}
QListWidget::item {{
    padding: 8px 14px;
    border-radius: 4px;
    margin: 2px 4px;
}}
QListWidget::item:selected {{
    background-color: {Color.SELECTION_BG};
    color: {Color.TEXT_PRIMARY};
}}
QListWidget::item:hover:!selected {{
    background-color: {Color.SURFACE_3};
}}

/* =================================================================
   按钮系统
   ================================================================= */
QPushButton {{
    background-color: {Color.PRIMARY};
    color: #ffffff;
    border: none;
    padding: 7px 18px;
    border-radius: 6px;
    min-height: 24px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {Color.PRIMARY_HOVER};
}}
QPushButton:pressed {{
    background-color: {Color.PRIMARY_PRESSED};
}}
QPushButton:disabled {{
    background-color: {Color.SURFACE_4};
    color: {Color.TEXT_MUTED};
}}

/* 次要按钮 */
QPushButton.secondary {{
    background-color: {Color.SURFACE_4};
    color: {Color.TEXT_PRIMARY};
    border: 1px solid {Color.BORDER_LIGHT};
}}
QPushButton.secondary:hover {{
    background-color: {Color.SURFACE_3};
    border-color: {Color.TEXT_MUTED};
}}
QPushButton.secondary:pressed {{
    background-color: {Color.SURFACE_2};
}}

/* 幽灵按钮 (无背景，悬停显示) */
QPushButton.ghost {{
    background-color: {Color.TRANSPARENT};
    color: {Color.TEXT_SECONDARY};
    padding: 4px 12px;
}}
QPushButton.ghost:hover {{
    background-color: {Color.SURFACE_3};
    color: {Color.TEXT_PRIMARY};
}}

/* 危险按钮 */
QPushButton.danger {{
    background-color: {Color.DANGER};
    color: #ffffff;
}}
QPushButton.danger:hover {{
    background-color: {Color.DANGER_HOVER};
}}
QPushButton.danger:pressed {{
    background-color: #C0392B;
}}

/* 成功按钮 */
QPushButton.success {{
    background-color: {Color.SUCCESS};
    color: #ffffff;
}}
QPushButton.success:hover {{
    background-color: {Color.SUCCESS_HOVER};
}}

/* =================================================================
   输入框
   ================================================================= */
QLineEdit {{
    background-color: {Color.SURFACE_4};
    border: 1px solid {Color.BORDER_LIGHT};
    border-radius: 6px;
    padding: 7px 12px;
    color: {Color.TEXT_PRIMARY};
    selection-background-color: {Color.SELECTION_BG};
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {Color.BORDER_FOCUS};
}}
QLineEdit:disabled {{
    background-color: {Color.SURFACE_2};
    color: {Color.TEXT_MUTED};
}}

QTextEdit, QPlainTextEdit {{
    background-color: {Color.SURFACE_1};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
    padding: 10px 14px;
    color: {Color.TEXT_PRIMARY};
    selection-background-color: {Color.SELECTION_BG};
    font-size: 13px;
    line-height: 1.7;
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {Color.BORDER_FOCUS};
}}

/* 大纲编辑器 (OutlineEditor) */
QTextEdit.outline-editor {{
    background-color: {Color.SURFACE_2};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
    padding: 12px;
    font-size: 14px;
    line-height: 1.8;
}}
QTextEdit.outline-editor:focus {{
    border-color: {Color.BORDER_FOCUS};
}}

/* 章节内容编辑区 (ChapterEditor) */
QTextEdit.chapter-content {{
    font-size: 14px;
    line-height: 1.9;
}}

/* =================================================================
   标签
   ================================================================= */
QLabel {{
    color: {Color.TEXT_PRIMARY};
    background: transparent;
}}
QLabel.title {{
    font-size: 18px;
    font-weight: 600;
    color: {Color.TEXT_PRIMARY};
    letter-spacing: 0.3px;
}}
QLabel.subtitle {{
    font-size: 14px;
    color: {Color.TEXT_SECONDARY};
}}
QLabel.section {{
    font-size: 15px;
    font-weight: 600;
    color: {Color.TEXT_PRIMARY};
    padding: 6px 0;
    border-bottom: 1px solid {Color.BORDER};
}}
QLabel.muted {{
    font-size: 12px;
    color: {Color.TEXT_MUTED};
}}
QLabel.timestamp {{
    font-size: 11px;
    color: {Color.TEXT_MUTED};
}}

/* =================================================================
   分组框
   ================================================================= */
QGroupBox {{
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
    margin-top: 14px;
    padding: 18px 14px 14px;
    font-weight: 500;
    font-size: 13px;
    color: {Color.TEXT_SECONDARY};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: {Color.TEXT_PRIMARY};
}}

/* =================================================================
   分割器
   ================================================================= */
QSplitter::handle {{
    background-color: {Color.BORDER};
    width: 1px;
}}
QSplitter::handle:hover {{
    background-color: {Color.PRIMARY};
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* =================================================================
   标签页
   ================================================================= */
QTabWidget::pane {{
    border: none;
    background-color: {Color.SURFACE_1};
}}
QTabBar::tab {{
    background-color: {Color.SURFACE_2};
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 22px;
    margin-right: 2px;
    color: {Color.TEXT_SECONDARY};
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}}
QTabBar::tab:selected {{
    background-color: {Color.SURFACE_1};
    border-bottom: 2px solid {Color.PRIMARY};
    color: {Color.TEXT_PRIMARY};
}}
QTabBar::tab:hover:!selected {{
    background-color: {Color.SURFACE_3};
    color: {Color.TEXT_PRIMARY};
}}

/* =================================================================
   滚动条
   ================================================================= */
QScrollBar:vertical {{
    background-color: {Color.SURFACE_0};
    width: 8px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {Color.SCROLLBAR_HANDLE};
    border-radius: 4px;
    min-height: 30px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {Color.SCROLLBAR_HOVER};
    min-width: 10px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {Color.SURFACE_0};
    height: 8px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {Color.SCROLLBAR_HANDLE};
    border-radius: 4px;
    min-width: 30px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {Color.SCROLLBAR_HOVER};
    min-height: 10px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* =================================================================
   表格 (角色列表等)
   ================================================================= */
QTableWidget {{
    background-color: {Color.SURFACE_2};
    border: 1px solid {Color.BORDER};
    border-radius: 6px;
    gridline-color: {Color.BORDER};
    selection-background-color: {Color.SELECTION_BG};
    outline: none;
}}
QTableWidget::item {{
    padding: 6px 12px;
    border-bottom: 1px solid {Color.BORDER};
}}
QTableWidget::item:selected {{
    background-color: {Color.SELECTION_BG};
    color: {Color.TEXT_PRIMARY};
}}
QTableWidget::item:hover:!selected {{
    background-color: {Color.SURFACE_3};
}}
QHeaderView::section {{
    background-color: {Color.SURFACE_3};
    border: none;
    border-bottom: 1px solid {Color.BORDER};
    border-right: 1px solid {Color.BORDER};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
    color: {Color.TEXT_SECONDARY};
    text-transform: uppercase;
}}

/* =================================================================
   消息气泡 (Chat)
   ================================================================= */
QLabel.message-user {{
    background-color: {Color.SELECTION_BG};
    border-radius: 8px;
    padding: 10px 16px;
    color: {Color.TEXT_PRIMARY};
    font-size: 13px;
    line-height: 1.7;
}}
QLabel.message-assistant {{
    background-color: {Color.SURFACE_2};
    border-radius: 8px;
    padding: 10px 16px;
    color: {Color.TEXT_PRIMARY};
    font-size: 13px;
    line-height: 1.7;
}}

/* =================================================================
   Tooltip
   ================================================================= */
QToolTip {{
    background-color: {Color.SURFACE_3};
    border: 1px solid {Color.BORDER_LIGHT};
    padding: 6px 12px;
    border-radius: 4px;
    color: {Color.TEXT_PRIMARY};
    font-size: 12px;
}}

/* =================================================================
   对话框
   ================================================================= */
QDialog {{
    background-color: {Color.SURFACE_1};
}}
QMessageBox {{
    background-color: {Color.SURFACE_1};
}}
QMessageBox QLabel {{
    color: {Color.TEXT_PRIMARY};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    min-width: 80px;
}}

/* =================================================================
   滚动区域
   ================================================================= */
QScrollArea {{
    background: {Color.SURFACE_0};
    border: none;
}}

/* =================================================================
   输入框底部容器 (ChatPanel)
   ================================================================= */
QWidget.input-area {{
    background-color: {Color.SURFACE_2};
    border-top: 1px solid {Color.BORDER};
}}

/* =================================================================
   聊天输入框 (ChatPanel)
   ================================================================= */
QTextEdit.chat-input {{
    background-color: {Color.SURFACE_4};
    border: 1px solid {Color.BORDER_LIGHT};
    border-radius: 6px;
    padding: 8px 12px;
    color: {Color.TEXT_PRIMARY};
    font-size: 13px;
    min-height: 36px;
    max-height: 80px;
}}
QTextEdit.chat-input:focus {{
    border-color: {Color.BORDER_FOCUS};
}}

/* =================================================================
   发送按钮 (ChatPanel)
   ================================================================= */
QPushButton.send-button {{
    background-color: {Color.PRIMARY};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
    min-width: 72px;
    min-height: 36px;
}}
QPushButton.send-button:hover {{
    background-color: {Color.PRIMARY_HOVER};
}}
QPushButton.send-button:pressed {{
    background-color: {Color.PRIMARY_PRESSED};
}}

/* =================================================================
   下拉框
   ================================================================= */
QComboBox {{
    background-color: {Color.SURFACE_4};
    border: 1px solid {Color.BORDER_LIGHT};
    border-radius: 6px;
    padding: 6px 12px;
    color: {Color.TEXT_PRIMARY};
    font-size: 13px;
    min-height: 20px;
}}
QComboBox:focus {{
    border-color: {Color.BORDER_FOCUS};
}}
QComboBox:hover {{
    border-color: {Color.TEXT_MUTED};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {Color.SURFACE_2};
    border: 1px solid {Color.BORDER};
    selection-background-color: {Color.SELECTION_BG};
    selection-color: {Color.TEXT_PRIMARY};
    color: {Color.TEXT_PRIMARY};
    padding: 4px;
    outline: none;
}}
"""

# 导出 Color 类供其他模块使用
__all__ = ["APP_STYLE", "Color"]
