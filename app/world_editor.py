"""
世界观编辑器 — 管理故事的世界设定
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QGroupBox,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from features.novel import manager


class WorldEditor(QWidget):
    """世界观设定编辑器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_story_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 标题
        self.story_label = QLabel("未选择故事")
        self.story_label.setProperty("class", "section")
        main_layout.addWidget(self.story_label)

        # 世界观名称
        main_layout.addWidget(QLabel("🌍 世界观名称"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：中土世界、银河帝国、魔法大陆...")
        main_layout.addWidget(self.name_edit)

        # 世界观描述
        main_layout.addWidget(QLabel("📖 世界观描述"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMinimumHeight(80)
        self.desc_edit.setPlaceholderText(
            "描述这个世界的整体面貌、时代背景、文明程度..."
        )
        main_layout.addWidget(self.desc_edit)

        # 世界规则
        main_layout.addWidget(QLabel("⚡ 世界规则 / 特殊设定"))
        self.rules_edit = QTextEdit()
        self.rules_edit.setMinimumHeight(80)
        self.rules_edit.setPlaceholderText(
            "魔法体系、科技限制、种族设定、自然法则...\n这个世界有哪些独特的规则？"
        )
        main_layout.addWidget(self.rules_edit)

        # 历史背景
        main_layout.addWidget(QLabel("📜 历史背景"))
        self.history_edit = QTextEdit()
        self.history_edit.setMinimumHeight(80)
        self.history_edit.setPlaceholderText(
            "这个世界的重大历史事件、传说、战争...\n过去的哪些事情塑造了现在的世界？"
        )
        main_layout.addWidget(self.history_edit)

        # 保存按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾 保存世界观")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

        main_layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def load_story(self, story_id: str):
        """加载世界观"""
        self._current_story_id = story_id
        story = manager.get_story(story_id)
        if not story:
            self.story_label.setText("故事不存在")
            return
        self.story_label.setText(f"📖 {story['title']} — 世界观设定")

        world = story.get("world", {})
        self.name_edit.setText(world.get("name", ""))
        self.desc_edit.setPlainText(world.get("description", ""))
        self.rules_edit.setPlainText(world.get("rules", ""))
        self.history_edit.setPlainText(world.get("background", ""))

    def _on_save(self):
        if not self._current_story_id:
            return
        manager.update_world(
            self._current_story_id,
            name=self.name_edit.text().strip(),
            description=self.desc_edit.toPlainText().strip(),
            rules=self.rules_edit.toPlainText().strip(),
            background=self.history_edit.toPlainText().strip(),
        )
        QMessageBox.information(self, "成功", "世界观已保存")
