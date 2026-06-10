"""
天机 - 对话记忆管理模块
支持滑动窗口、多种记忆策略、持久化存储
"""

import json
import os
from datetime import datetime
from typing import Optional

from ..config import config
from ..utils.helpers import setup_logger

logger = setup_logger("天机.Memory")


class Message:
    """单条对话消息"""

    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role  # "user", "assistant", "system"
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp"),
        )

    def __repr__(self) -> str:
        return f"<Message {self.role}: {self.content[:50]}...>"


class ConversationMemory:
    """
    对话记忆管理器
    - 滑动窗口：保留最近 N 轮对话
    - 持久化：可保存/加载到 JSON 文件
    - 系统提示词保护：始终保留最前面的系统消息
    """

    def __init__(self):
        self.max_turns = config.memory_max_turns
        self.persistent = config.memory_persistent
        self.storage_path = config.memory_storage_path

        # 内部存储: [Message, ...]
        self._messages: list[Message] = []

        # 如果开启持久化且文件存在，加载历史
        if self.persistent and os.path.exists(self.storage_path):
            self._load()
            logger.debug(f"已加载 {len(self._messages)} 条历史记忆")

    @property
    def messages(self) -> list[dict]:
        """获取 LLM 格式的消息列表 (list[dict])"""
        return [m.to_dict() for m in self._messages]

    @property
    def api_messages(self) -> list[dict]:
        """
        获取用于 API 调用的消息列表
        （只包含 role 和 content，不包含 timestamp）
        """
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def add_message(self, role: str, content: str):
        """添加一条消息"""
        msg = Message(role, content)
        self._messages.append(msg)
        self._trim()
        if self.persistent:
            self._save()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("assistant", content)

    def add_system_message(self, content: str):
        """添加系统消息（插在最前面）"""
        msg = Message("system", content)
        # 找到最后一个系统消息的位置，插入其后
        last_sys_idx = -1
        for i, m in enumerate(self._messages):
            if m.role == "system":
                last_sys_idx = i
        self._messages.insert(last_sys_idx + 1, msg)
        self._trim()
        if self.persistent:
            self._save()

    def set_system_prompt(self, content: str):
        """设置/替换系统提示词"""
        # 移除所有已存在的系统消息
        self._messages = [m for m in self._messages if m.role != "system"]
        # 在开头插入新系统消息
        self._messages.insert(0, Message("system", content))
        if self.persistent:
            self._save()

    def _trim(self):
        """
        修剪记忆窗口
        策略：始终保留 system 消息，然后从最早的 user/assistant 开始丢弃
        """
        system_msgs = [m for m in self._messages if m.role == "system"]
        non_system = [m for m in self._messages if m.role != "system"]

        # non_system 按对话轮次切割（一对 user+assistant 算一轮）
        # 保留最近的 max_turns 轮
        max_pairs = self.max_turns
        if len(non_system) > max_pairs * 2:
            # 丢弃最旧的消息
            excess = len(non_system) - max_pairs * 2
            non_system = non_system[excess:]

        self._messages = system_msgs + non_system

    def clear(self):
        """清空所有记忆（保留系统提示词）"""
        system_msgs = [m for m in self._messages if m.role == "system"]
        self._messages = system_msgs
        if self.persistent:
            self._save()

    def clear_all(self):
        """完全清空"""
        self._messages = []
        if self.persistent:
            self._save()

    def get_history_text(self, max_turns: Optional[int] = None) -> str:
        """获取可读的对话历史文本"""
        turns = max_turns or self.max_turns
        lines = []
        for m in self._messages[-turns * 2 :]:
            role_label = {"user": "用户", "assistant": "助手", "system": "系统"}.get(
                m.role, m.role
            )
            lines.append(f"[{role_label}] {m.content}")
        return "\n".join(lines)

    def count_messages(self) -> int:
        """消息总数"""
        return len(self._messages)

    def _save(self):
        """持久化到文件"""
        try:
            data = {
                "max_turns": self.max_turns,
                "messages": [m.to_dict() for m in self._messages],
                "saved_at": datetime.now().isoformat(),
            }
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存记忆失败: {e}")

    def _load(self):
        """从文件加载记忆"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for msg_data in data.get("messages", []):
                self._messages.append(Message.from_dict(msg_data))
        except Exception as e:
            logger.warning(f"加载记忆失败: {e}")

    def __len__(self) -> int:
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)
