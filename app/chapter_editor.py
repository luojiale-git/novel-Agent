"""
章节编辑器 — 写作核心区域
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from app.toast import Toast
from features.novel import manager


class ChapterEditor(QWidget):
    """章节编辑器：左侧章节列表 + 右侧编辑区"""

    chapter_saved = Signal(str)  # 发出 chapter_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_story_id: str = ""
        self._editing_chapter_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        self.story_label = QLabel("未选择故事")
        self.story_label.setProperty("class", "section")
        toolbar.addWidget(self.story_label)
        toolbar.addStretch()

        self.new_chapter_btn = QPushButton("+ 新章节")
        self.new_chapter_btn.clicked.connect(self._on_new_chapter)
        toolbar.addWidget(self.new_chapter_btn)

        main_layout.addLayout(toolbar)

        # 分割器：左侧章节列表 | 右侧编辑器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：章节列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(4)

        left_layout.addWidget(QLabel("📑 章节"))

        self.chapter_list = QListWidget()
        self.chapter_list.itemClicked.connect(self._on_chapter_selected)
        left_layout.addWidget(self.chapter_list)

        del_btn = QPushButton("删除选中")
        del_btn.setProperty("class", "secondary")
        del_btn.clicked.connect(self._on_delete_chapter)
        left_layout.addWidget(del_btn)

        splitter.addWidget(left_panel)

        # 右侧：编辑器
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(6)

        # 章节标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("输入章节标题...")
        title_layout.addWidget(self.title_edit)
        right_layout.addLayout(title_layout)

        # 正文
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("在此书写章节内容...")
        font = QFont("Microsoft YaHei UI", 12)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.content_edit.setFont(font)
        self.content_edit.setProperty("class", "chapter-content")
        right_layout.addWidget(self.content_edit)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾 保存章节")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def load_story(self, story_id: str):
        """加载故事章节"""
        self._current_story_id = story_id
        self._editing_chapter_id = ""
        self.title_edit.clear()
        self.content_edit.clear()
        self.new_chapter_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

        story = manager.get_story(story_id)
        if story:
            self.story_label.setText(f"📖 {story['title']} — 章节编辑")
            self._refresh_chapter_list(story.get("chapters", []))
        else:
            self.story_label.setText("故事不存在")

    def _refresh_chapter_list(self, chapters: list):
        self.chapter_list.clear()
        for ch in chapters:
            item = QListWidgetItem(f"📄 {ch['title']}")
            item.setData(Qt.UserRole, ch["id"])
            self.chapter_list.addItem(item)

    def _on_new_chapter(self):
        if not self._current_story_id:
            return
        title = "新章节"
        ch = manager.add_chapter(self._current_story_id, title, "")
        if ch:
            story = manager.get_story(self._current_story_id)
            self._refresh_chapter_list(story.get("chapters", []))
            self._load_chapter(ch["id"])

    def _on_chapter_selected(self, item):
        chapter_id = item.data(Qt.UserRole)
        self._load_chapter(chapter_id)

    def _load_chapter(self, chapter_id: str):
        self._editing_chapter_id = chapter_id
        ch = manager.get_chapter(self._current_story_id, chapter_id)
        if ch:
            self.title_edit.setText(ch.get("title", ""))
            self.content_edit.setPlainText(ch.get("content", ""))

    def _on_save(self):
        if not self._current_story_id or not self._editing_chapter_id:
            Toast.show("请先选择或创建一个章节", Toast.WARNING)
            return
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText()
        if not title:
            Toast.show("章节标题不能为空", Toast.WARNING)
            return
        result = manager.update_chapter(
            self._current_story_id,
            self._editing_chapter_id,
            title=title,
            content=content,
        )
        if result:
            self.chapter_saved.emit(self._editing_chapter_id)
            # 刷新列表标题
            story = manager.get_story(self._current_story_id)
            self._refresh_chapter_list(story.get("chapters", []))
            Toast.show("章节已保存", Toast.SUCCESS)

    def _on_delete_chapter(self):
        item = self.chapter_list.currentItem()
        if not item or not self._current_story_id:
            return
        chapter_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除此章节吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            manager.delete_chapter(self._current_story_id, chapter_id)
            self._editing_chapter_id = ""
            self.title_edit.clear()
            self.content_edit.clear()
            story = manager.get_story(self._current_story_id)
            self._refresh_chapter_list(story.get("chapters", []))
