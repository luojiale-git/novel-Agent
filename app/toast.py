"""
Toast 通知组件 — 轻量级的非侵入式消息提示

用法:
    Toast.show(parent, "已保存", Toast.SUCCESS)
    Toast.show(parent, "操作失败", Toast.ERROR)
    Toast.show(parent, "提示信息", Toast.INFO)
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QHBoxLayout,
    QGraphicsOpacityEffect,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont

from app.styles import Color


class Toast(QWidget):
    """底部弹出式通知，2.5 秒自动消失"""

    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

    _instances: list["Toast"] = []

    def __init__(
        self,
        text: str,
        toast_type: str = INFO,
        duration: int = 2500,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._duration = duration
        self._toast_type = toast_type
        self._setup_ui(text, toast_type)
        self._setup_animation()

        # 设置窗口标志 — 无边框、置顶、不抢焦点
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _setup_ui(self, text: str, toast_type: str):
        # 根据类型设置颜色
        bg_color = {
            self.SUCCESS: Color.SUCCESS,
            self.ERROR: Color.DANGER,
            self.INFO: Color.PRIMARY,
            self.WARNING: Color.ACCENT_GOLD,
        }.get(toast_type, Color.SURFACE_3)

        icon = {
            self.SUCCESS: "✓",
            self.ERROR: "✕",
            self.INFO: "●",
            self.WARNING: "▲",
        }.get(toast_type, "●")

        self.setStyleSheet(f"""
            Toast {{
                background-color: {bg_color};
                border-radius: 8px;
                padding: 0px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 18, 10)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.9);
            font-size: 15px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(icon_label)

        text_label = QLabel(text)
        text_label.setStyleSheet("""
            color: #ffffff;
            font-size: 13px;
            font-weight: 500;
            background: transparent;
        """)
        text_label.setWordWrap(False)
        layout.addWidget(text_label)

        self.adjustSize()

    def _setup_animation(self):
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_out.finished.connect(self.close)

    def _show_widget(self):
        """内部方法：显示 widget 并启动定时消失"""
        super().show()
        # 自动定位到父窗口底部中央
        self._reposition()
        # 定时自动消失
        QTimer.singleShot(self._duration, self._start_fade_out)

    def _reposition(self):
        parent = self.parent()
        if parent:
            parent_rect = parent.geometry()
            global_pos = parent.mapToGlobal(QPoint(0, 0))
            x = global_pos.x() + (parent_rect.width() - self.width()) // 2
            y = global_pos.y() + parent_rect.height() - self.height() - 40
            self.move(x, y)

    def _start_fade_out(self):
        if self._fade_out:
            self._fade_out.start()

    def mousePressEvent(self, event):
        """点击立即关闭"""
        self.close()
        super().mousePressEvent(event)

    @classmethod
    def show(cls, text: str, toast_type: str = INFO, duration: int = 2500):
        """全局便捷方法 — 自动寻找主窗口作为父窗口"""
        parent = None
        # 找当前激活的主窗口
        active = QApplication.activeWindow()
        if active:
            parent = active.window()
        if not parent:
            for w in QApplication.topLevelWidgets():
                if w.isVisible() and w.windowTitle():
                    parent = w
                    break

        toast = cls(text, toast_type, duration, parent)

        # 堆叠显示：如果已有 toast，往上偏移
        offset = 0
        for t in cls._instances:
            if t.isVisible():
                offset += 48
        toast._offset = offset
        cls._instances.append(toast)

        toast._show_widget()

        # 清理已关闭的实例
        cls._instances = [t for t in cls._instances if t.isVisible()]

    def moveEvent(self, event):
        """应用堆叠偏移"""
        super().moveEvent(event)
        if hasattr(self, "_offset") and self._offset:
            self.move(self.x(), self.y() - self._offset)

    def closeEvent(self, event):
        if self in self._instances:
            self._instances.remove(self)
        super().closeEvent(event)


def toast(text: str, toast_type: str = Toast.INFO, duration: int = 2500):
    """快捷函数"""
    Toast.show(text, toast_type, duration)
