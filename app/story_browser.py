"""
故事浏览器 — 左侧故事列表
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QInputDialog,
    QMessageBox,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from features.novel import manager


class StoryBrowser(QWidget):
    """故事列表浏览器"""

    story_selected = Signal(str)  # 发出 story_id
    story_created = Signal(str)  # 发出 story_id
    story_deleted = Signal()  # 无参数

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 标题
        title = QLabel("📚 我的故事")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # 新建按钮
        self.new_btn = QPushButton("➕ 新故事")
        self.new_btn.clicked.connect(self._on_new_story)
        layout.addWidget(self.new_btn)

        # 故事列表
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def refresh(self):
        """刷新故事列表"""
        self.list_widget.clear()
        stories = manager.list_stories()
        for s in stories:
            item = QListWidgetItem()
            title = s.get("title", "未命名")
            genre = s.get("genre", "")
            label = f"📖 {title}"
            if genre:
                label += f"  [{genre}]"
            item.setText(label)
            item.setData(Qt.UserRole, s["id"])
            item.setToolTip(f"ID: {s['id']}\n更新: {s.get('updated_at', '')[:10]}")
            self.list_widget.addItem(item)

    def _on_new_story(self):
        title, ok = QInputDialog.getText(self, "新建故事", "故事标题:")
        if not ok or not title.strip():
            return
        genre, ok = QInputDialog.getText(self, "新建故事", "故事类型 (可选):")
        genre = genre.strip() if ok else ""
        story = manager.create_story(title.strip(), genre)
        self.refresh()
        self.story_created.emit(story["id"])

    def _on_item_clicked(self, item):
        story_id = item.data(Qt.UserRole)
        if story_id:
            self.story_selected.emit(story_id)

    def _on_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        story_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        # 删除操作
        del_action = QAction("🗑 删除故事", self)
        del_action.triggered.connect(lambda: self._delete_story(story_id))
        menu.addAction(del_action)
        menu.exec(self.list_widget.mapToGlobal(pos))

    def _delete_story(self, story_id: str):
        story = manager.get_story(story_id)
        if not story:
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除故事《{story['title']}》吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            manager.delete_story(story_id)
            self.refresh()
            self.story_deleted.emit()
