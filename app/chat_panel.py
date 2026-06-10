"""
聊天对话面板 — 与天机 Agent 对话的界面
"""

import re
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QScrollArea,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QThread, QSize, QTimer
from PySide6.QtGui import QFont, QTextCursor


class ChatWorker(QThread):
    """后台执行 Agent 推理，防止 UI 卡顿"""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, agent, message: str):
        super().__init__()
        self.agent = agent
        self.message = message

    def run(self):
        try:
            result = self.agent.run(self.message)
            self.finished.emit(str(result))
        except Exception as e:
            self.error.emit(str(e))


class MessageBubble(QFrame):
    """单条消息气泡"""

    def __init__(self, text: str, role: str, timestamp: str = ""):
        super().__init__()
        self.role = role
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # 头部：角色 + 时间
        header = QLabel(
            f"<b>{'🧑 你' if role == 'user' else '🤖 天机'}</b>  {self.timestamp}"
        )
        header.setProperty("class", "timestamp")
        layout.addWidget(header)

        # 内容
        content = QLabel(text)
        content.setWordWrap(True)
        content.setTextFormat(Qt.TextFormat.RichText)
        content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        content.setProperty("class", f"message-{role}")
        # 滚动时自动调整宽度
        content.setMinimumWidth(200)
        content.setMaximumWidth(600)
        layout.addWidget(content)


class ChatPanel(QWidget):
    """聊天面板：消息列表 + 输入框 + 发送按钮"""

    def __init__(self, agent=None, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.messages: list[dict] = []
        self._worker = None
        self._setup_ui()

    def set_agent(self, agent):
        self.agent = agent

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 消息滚动区域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setProperty("class", "chat-scroll")

        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_layout.setContentsMargins(12, 8, 12, 8)
        self.message_layout.setSpacing(8)
        self.message_layout.addStretch()

        self.scroll.setWidget(self.message_container)

        # 欢迎消息
        self._add_banner()

        # 底部输入区
        input_container = QWidget()
        input_container.setProperty("class", "input-area")

        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 8, 12, 8)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入消息，按 Enter 发送...")
        self.input_edit.setMaximumHeight(80)
        self.input_edit.setMinimumHeight(36)
        self.input_edit.setAcceptRichText(False)
        self.input_edit.installEventFilter(self)
        self.input_edit.setProperty("class", "chat-input")

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(72, 36)
        self.send_btn.setProperty("class", "send-button")
        self.send_btn.clicked.connect(self._on_send)

        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(self.scroll)
        layout.addWidget(input_container)

    def _add_banner(self):
        banner = QLabel(
            "<div style='text-align:center; padding: 20px;'>"
            "<h2 style='color: #e0e0e0; margin: 0;'>天机 · 小说创作助手</h2>"
            "<p style='color: #888; margin: 8px 0 0 0;'>"
            "与 AI 对话来创作你的故事吧！<br>"
            "输入任意创作想法，天机会帮你展开。</p>"
            "</div>"
        )
        banner.setWordWrap(True)
        banner.setTextFormat(Qt.TextFormat.RichText)
        banner.setAlignment(Qt.AlignCenter)
        self.message_layout.insertWidget(0, banner)

    def _on_send(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        self.input_edit.clear()
        self._add_message(text, "user")
        self._thinking()

    def _add_message(self, text: str, role: str):
        msg = MessageBubble(text, role)
        # 插入到 stretch 前面
        self.message_layout.insertWidget(self.message_layout.count() - 1, msg)
        self.messages.append({"role": role, "text": text})
        # 滚动到底部
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _thinking(self):
        """显示思考中指示器"""
        self.send_btn.setEnabled(False)
        self.send_btn.setText("思考中...")
        self.input_edit.setEnabled(False)

        self._thinking_label = QLabel(
            "<div style='padding: 8px 12px; color: #888;'>"
            "<i>🤔 天机正在思考...</i></div>"
        )
        self._thinking_label.setProperty("class", "thinking")
        self.message_layout.insertWidget(
            self.message_layout.count() - 1, self._thinking_label
        )
        self._scroll_to_bottom()

        # 启动后台线程
        if self.agent:
            self._worker = ChatWorker(self.agent, self.messages[-1]["text"])
            self._worker.finished.connect(self._on_response)
            self._worker.error.connect(self._on_error)
            self._worker.start()

    def _on_response(self, text: str):
        self._remove_thinking()
        self._add_message(text, "assistant")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self.input_edit.setEnabled(True)
        self.input_edit.setFocus()

    def _on_error(self, err: str):
        self._remove_thinking()
        self._add_message(f"⚠️ {err}", "assistant")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")
        self.input_edit.setEnabled(True)

    def _remove_thinking(self):
        if hasattr(self, "_thinking_label") and self._thinking_label:
            self._thinking_label.deleteLater()
            self._thinking_label = None

    def _scroll_to_bottom(self):
        scrollbar = self.scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def reset(self):
        """清空对话"""
        # 保留 banner
        for i in range(self.message_layout.count() - 2, -1, -1):
            item = self.message_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if not isinstance(w, QLabel) or not w.text().startswith("<div"):
                    w.deleteLater()
        self.messages.clear()

    def eventFilter(self, obj, event):
        """捕获 Enter 键发送消息"""
        if obj is self.input_edit and event.type() == event.Type.KeyPress:
            if (
                event.key() == Qt.Key_Return
                and not event.modifiers() & Qt.ShiftModifier
            ):
                self._on_send()
                return True
        return super().eventFilter(obj, event)
