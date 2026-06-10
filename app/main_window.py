"""
天机主窗口 — 整合所有面板的应用主界面
"""

import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QWidget,
    QVBoxLayout,
    QMenuBar,
    QMenu,
    QStatusBar,
    QMessageBox,
    QInputDialog,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon

from app.styles import APP_STYLE
from app.story_browser import StoryBrowser
from app.chat_panel import ChatPanel
from app.novel_panel import NovelPanel
from features.novel import manager


class MainWindow(QMainWindow):
    """天机桌面主窗口"""

    def __init__(self, agent=None):
        super().__init__()
        self.agent = agent
        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_window(self):
        self.setWindowTitle("天机 · AI 小说创作助手")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        # 居中
        from PySide6.QtGui import QScreen

        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo = self.geometry()
        geo.moveCenter(center)
        self.setGeometry(geo)

    def _setup_menu(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        new_action = QAction("新建故事", self)
        new_action.triggered.connect(self._on_new_story)
        file_menu.addAction(new_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        clear_chat_action = QAction("清空对话", self)
        clear_chat_action.triggered.connect(self._on_clear_chat)
        edit_menu.addAction(clear_chat_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        toggle_sidebar_action = QAction("切换左侧面板", self)
        toggle_sidebar_action.setCheckable(True)
        toggle_sidebar_action.setChecked(True)
        toggle_sidebar_action.triggered.connect(self._on_toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于天机", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 主分割器：左侧故事浏览器 | 右侧: 上(聊天)下(创作区) 或 右分割
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)

        # 左侧：故事浏览器
        self.story_browser = StoryBrowser()
        self.story_browser.setMinimumWidth(180)
        self.story_browser.setMaximumWidth(300)
        main_splitter.addWidget(self.story_browser)

        # 右侧：上下分割
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(2)

        # 上方：聊天面板
        self.chat_panel = ChatPanel(agent=self.agent)
        chat_min_height = 200
        self.chat_panel.setMinimumHeight(chat_min_height)
        right_splitter.addWidget(self.chat_panel)

        # 下方：小说创作工作区
        self.novel_panel = NovelPanel()
        right_splitter.addWidget(self.novel_panel)

        # 初始比例：聊天 35%，创作区 65%
        right_splitter.setSizes([300, 550])

        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        layout.addWidget(main_splitter)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("就绪")

    def _connect_signals(self):
        self.story_browser.story_selected.connect(self._on_story_selected)
        self.story_browser.story_created.connect(self._on_story_selected)
        self.story_browser.story_deleted.connect(self._on_story_deleted)

    # ========== Slots ==========

    def _on_new_story(self):
        """从菜单新建故事"""
        title, ok = QInputDialog.getText(self, "新建故事", "故事标题:")
        if not ok or not title.strip():
            return
        genre, ok = QInputDialog.getText(self, "新建故事", "故事类型 (可选):")
        genre = genre.strip() if ok else ""
        story = manager.create_story(title.strip(), genre)
        self.story_browser.refresh()
        self._on_story_selected(story["id"])

    def _on_story_selected(self, story_id: str):
        """选中故事"""
        story = manager.get_story(story_id)
        if not story:
            return
        self.novel_panel.load_story(story_id)
        self.statusbar.showMessage(f"当前故事: {story['title']}")

    def _on_story_deleted(self):
        """故事被删除"""
        self.statusbar.showMessage("故事已删除")
        # 清空创作区
        self.novel_panel.info_bar.setText("请从左侧选择或创建一个故事")

    def _on_clear_chat(self):
        """清空聊天"""
        reply = QMessageBox.question(
            self,
            "清空对话",
            "确定要清空当前对话吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.chat_panel.reset()
            self.statusbar.showMessage("对话已清空")

    def _on_toggle_sidebar(self, checked: bool):
        """切换左侧栏可见性"""
        self.story_browser.setVisible(checked)

    def _on_about(self):
        QMessageBox.about(
            self,
            "关于天机",
            "<h2>天机 · AI 小说创作助手</h2>"
            "<p>版本 1.0.0</p>"
            "<p>基于大语言模型的小说创作辅助工具。</p>"
            "<p>支持故事管理、章节编辑、角色设定、世界观构建。</p>",
        )


def launch_gui(agent=None):
    """启动 GUI 应用"""
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    window = MainWindow(agent=agent)
    window.show()

    sys.exit(app.exec())
