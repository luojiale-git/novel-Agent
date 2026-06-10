"""
小说创作工作区 — 整合章节、角色、世界观编辑器的标签面板
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QTextEdit,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal

from app.chapter_editor import ChapterEditor
from app.character_editor import CharacterEditor
from app.world_editor import WorldEditor
from app.toast import Toast


class OutlineEditor(QWidget):
    """大纲编辑器（嵌入在小说工作区中）"""

    outline_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_story_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(QLabel("📋 故事大纲"))
        self.outline_edit = QTextEdit()
        self.outline_edit.setPlaceholderText(
            "在此编写故事的整体大纲：\n"
            "- 主线剧情走向\n"
            "- 关键情节节点\n"
            "- 故事结构安排\n"
            "- 开篇、发展、高潮、结局\n"
            "..."
        )
        self.outline_edit.setProperty("class", "outline-editor")
        layout.addWidget(self.outline_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾 保存大纲")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def load_story(self, story_id: str):
        self._current_story_id = story_id
        from features.novel import manager

        story = manager.get_story(story_id)
        if story:
            self.outline_edit.setPlainText(story.get("outline", ""))

    def _on_save(self):
        if not self._current_story_id:
            return
        from features.novel import manager

        outline = self.outline_edit.toPlainText()
        manager.update_story(self._current_story_id, outline=outline)
        self.outline_saved.emit()
        Toast.show("大纲已保存", Toast.SUCCESS)


class NovelPanel(QWidget):
    """小说创作工作区 — 包含大纲/章节/角色/世界观的标签页"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_story_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部信息
        self.info_bar = QLabel("请从左侧选择或创建一个故事")
        self.info_bar.setProperty("class", "info-bar")
        layout.addWidget(self.info_bar)

        # 标签页
        self.tab_widget = QTabWidget()

        # 大纲
        self.outline_editor = OutlineEditor()
        self.tab_widget.addTab(self.outline_editor, "📋 大纲")

        # 章节
        self.chapter_editor = ChapterEditor()
        self.tab_widget.addTab(self.chapter_editor, "📄 章节")

        # 角色
        self.character_editor = CharacterEditor()
        self.tab_widget.addTab(self.character_editor, "👥 角色")

        # 世界观
        self.world_editor = WorldEditor()
        self.tab_widget.addTab(self.world_editor, "🌍 世界观")

        layout.addWidget(self.tab_widget)

    def load_story(self, story_id: str):
        """加载故事到所有编辑器"""
        self._current_story_id = story_id
        from features.novel import manager

        story = manager.get_story(story_id)
        if story:
            self.info_bar.setText(
                f"📖 当前故事：{story['title']} ({story.get('genre', '未分类')})"
            )
            self.outline_editor.load_story(story_id)
            self.chapter_editor.load_story(story_id)
            self.character_editor.load_story(story_id)
            self.world_editor.load_story(story_id)
            self.tab_widget.setCurrentIndex(0)
        else:
            self.info_bar.setText("故事数据不存在")

    def get_current_story_id(self) -> str:
        return self._current_story_id
