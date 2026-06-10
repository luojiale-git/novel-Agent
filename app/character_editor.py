"""
角色编辑器 — 管理故事人物
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSplitter,
    QMessageBox,
    QHeaderView,
    QInputDialog,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from features.novel import manager


class CharacterEditor(QWidget):
    """角色编辑器：左侧表格 + 右侧详情编辑"""

    character_updated = Signal(str)  # 发出 char_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_story_id: str = ""
        self._editing_char_id: str = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 顶部
        self.story_label = QLabel("未选择故事")
        self.story_label.setProperty("class", "section")
        main_layout.addWidget(self.story_label)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：表格
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(4)

        left_layout.addWidget(QLabel("👥 人物列表"))

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["姓名", "角色", "特征"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemClicked.connect(self._on_row_clicked)
        left_layout.addWidget(self.table)

        add_btn = QPushButton("+ 添加人物")
        add_btn.clicked.connect(self._on_add)
        left_layout.addWidget(add_btn)

        del_btn = QPushButton("删除选中")
        del_btn.setProperty("class", "danger")
        del_btn.clicked.connect(self._on_delete)
        left_layout.addWidget(del_btn)

        splitter.addWidget(left_panel)

        # 右侧：详情编辑
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(6)

        right_layout.addWidget(QLabel("📝 人物详情"))

        # 姓名
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("姓名:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("人物姓名")
        row1.addWidget(self.name_edit)
        right_layout.addLayout(row1)

        # 角色
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("角色:"))
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("主角 / 反派 / 配角...")
        row2.addWidget(self.role_edit)
        right_layout.addLayout(row2)

        # 特征
        right_layout.addWidget(QLabel("性格特征:"))
        self.traits_edit = QTextEdit()
        self.traits_edit.setMaximumHeight(80)
        self.traits_edit.setPlaceholderText("描述人物的性格、习惯...")
        right_layout.addWidget(self.traits_edit)

        # 背景
        right_layout.addWidget(QLabel("背景故事:"))
        self.bg_edit = QTextEdit()
        self.bg_edit.setPlaceholderText("人物的过往经历、动机...")
        right_layout.addWidget(self.bg_edit)

        # 保存
        self.save_btn = QPushButton("💾 保存修改")
        self.save_btn.clicked.connect(self._on_save)
        right_layout.addWidget(self.save_btn)

        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def load_story(self, story_id: str):
        """加载故事的角色"""
        self._current_story_id = story_id
        self._editing_char_id = ""
        self._clear_detail()

        story = manager.get_story(story_id)
        if story:
            self.story_label.setText(f"📖 {story['title']} — 角色管理")
            self._refresh_table(story.get("characters", []))
        else:
            self.story_label.setText("故事不存在")

    def _refresh_table(self, characters: list):
        self.table.setRowCount(len(characters))
        for i, c in enumerate(characters):
            self.table.setItem(i, 0, QTableWidgetItem(c["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(c.get("role", "")))
            self.table.setItem(i, 2, QTableWidgetItem(c.get("traits", "")[:30]))
            # 存储 char_id
            self.table.item(i, 0).setData(Qt.UserRole, c["id"])

    def _on_row_clicked(self, item):
        row = item.row()
        char_id_item = self.table.item(row, 0)
        if not char_id_item:
            return
        char_id = char_id_item.data(Qt.UserRole)
        self._load_character(char_id)

    def _load_character(self, char_id: str):
        self._editing_char_id = char_id
        story = manager.get_story(self._current_story_id)
        if not story:
            return
        for c in story.get("characters", []):
            if c["id"] == char_id:
                self.name_edit.setText(c["name"])
                self.role_edit.setText(c.get("role", ""))
                self.traits_edit.setPlainText(c.get("traits", ""))
                self.bg_edit.setPlainText(c.get("background", ""))
                break

    def _clear_detail(self):
        self.name_edit.clear()
        self.role_edit.clear()
        self.traits_edit.clear()
        self.bg_edit.clear()

    def _on_add(self):
        if not self._current_story_id:
            return
        name, ok = QInputDialog.getText(self, "添加人物", "人物姓名:")
        if not ok or not name.strip():
            return
        char = manager.add_character(self._current_story_id, name.strip())
        if char:
            story = manager.get_story(self._current_story_id)
            self._refresh_table(story.get("characters", []))
            # 选中新添加的行
            for i in range(self.table.rowCount()):
                if self.table.item(i, 0).data(Qt.UserRole) == char["id"]:
                    self.table.selectRow(i)
                    self._load_character(char["id"])
                    break

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一个人物")
            return
        char_id = self.table.item(row, 0).data(Qt.UserRole)
        name = self.table.item(row, 0).text()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除人物「{name}」吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            manager.delete_character(self._current_story_id, char_id)
            self._clear_detail()
            self._editing_char_id = ""
            story = manager.get_story(self._current_story_id)
            self._refresh_table(story.get("characters", []))

    def _on_save(self):
        if not self._current_story_id or not self._editing_char_id:
            QMessageBox.information(self, "提示", "请先选择一个人物")
            return
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "姓名不能为空")
            return
        manager.update_character(
            self._current_story_id,
            self._editing_char_id,
            name=name,
            role=self.role_edit.text().strip(),
            traits=self.traits_edit.toPlainText().strip(),
            background=self.bg_edit.toPlainText().strip(),
        )
        self.character_updated.emit(self._editing_char_id)
        story = manager.get_story(self._current_story_id)
        self._refresh_table(story.get("characters", []))
        QMessageBox.information(self, "成功", "人物已保存")
