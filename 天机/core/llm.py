"""
天机 - LLM 接口抽象层
支持 DeepSeek / OpenAI / Ollama 三种后端，可扩展自定义后端
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Optional, Iterator

import requests

from ..config import config
from ..utils.helpers import setup_logger

logger = setup_logger("天机.LLM")


class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    @abstractmethod
    def chat(self, messages: list[dict], stream: bool = False) -> str | Iterator[str]:
        """发送对话消息并返回回复"""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """估算 token 数量"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """后端名称"""
        ...


class DeepSeekBackend(LLMBackend):
    """DeepSeek API 后端"""

    def __init__(self):
        self.base_url = config.llm_base_url
        self.api_key = config.llm_api_key
        self.model = config.llm_model
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens
        self.top_p = config.llm_top_p

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[dict], stream: bool = False) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": stream,
        }

    def chat(self, messages: list[dict], stream: bool = False) -> str | Iterator[str]:
        if not self.api_key:
            raise ValueError(
                "未配置 DeepSeek API Key。请设置环境变量 DEEPSEEK_API_KEY "
                "或在 config.yaml 中配置 llm.api_key"
            )

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        payload = self._build_payload(messages, stream)

        logger.debug(f"请求 DeepSeek: model={self.model}, messages={len(messages)}条")

        if stream:
            return self._stream_chat(url, payload)
        else:
            return self._sync_chat(url, payload)

    def _sync_chat(self, url: str, payload: dict) -> str:
        resp = requests.post(
            url, headers=self._get_headers(), json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _stream_chat(self, url: str, payload: dict) -> Iterator[str]:
        resp = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()

        for line in resp.iter_lines():
            if line:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    def count_tokens(self, text: str) -> int:
        # 简单估算：中文约 1.5 token/字，英文约 0.25 token/字符
        import re

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25) + 4

    @property
    def name(self) -> str:
        return "DeepSeek"


class OpenAIBackend(LLMBackend):
    """OpenAI API 后端"""

    def __init__(self):
        self.base_url = config.get("llm.base_url", "https://api.openai.com/v1")
        self.api_key = config.llm_api_key
        self.model = config.get("llm.model", "gpt-4")
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens
        self.top_p = config.llm_top_p

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages: list[dict], stream: bool = False) -> str | Iterator[str]:
        if not self.api_key:
            raise ValueError("未配置 OpenAI API Key")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stream": stream,
        }

        if stream:
            return self._stream_chat(url, payload)
        else:
            resp = requests.post(
                url, headers=self._get_headers(), json=payload, timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _stream_chat(self, url: str, payload: dict) -> Iterator[str]:
        resp = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            stream=True,
            timeout=120,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    def count_tokens(self, text: str) -> int:
        import re

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25) + 4

    @property
    def name(self) -> str:
        return "OpenAI"


class OllamaBackend(LLMBackend):
    """Ollama 本地后端"""

    def __init__(self):
        self.base_url = config.get("llm.base_url", "http://localhost:11434")
        self.model = config.get("llm.model", "qwen2:7b")
        self.temperature = config.llm_temperature

    def chat(self, messages: list[dict], stream: bool = False) -> str | Iterator[str]:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
            },
        }

        if stream:
            return self._stream_chat(url, payload)
        else:
            resp = requests.post(url, json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

    def _stream_chat(self, url: str, payload: dict) -> Iterator[str]:
        resp = requests.post(url, json=payload, stream=True, timeout=300)
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if data.get("done"):
                        break
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    def count_tokens(self, text: str) -> int:
        import re

        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars * 1.5 + other_chars * 0.25) + 4

    @property
    def name(self) -> str:
        return "Ollama"


class LLMFactory:
    """LLM 后端工厂"""

    _registry = {
        "deepseek": DeepSeekBackend,
        "openai": OpenAIBackend,
        "ollama": OllamaBackend,
    }

    @classmethod
    def register(cls, name: str, backend_cls: type[LLMBackend]):
        """注册自定义后端"""
        cls._registry[name.lower()] = backend_cls

    @classmethod
    def create(cls, backend_name: Optional[str] = None) -> LLMBackend:
        """创建 LLM 后端实例"""
        name = (backend_name or config.llm_backend).lower()
        if name not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"不支持的 LLM 后端: '{name}'。可用后端: {available}")
        instance = cls._registry[name]()
        logger.info(f"初始化 LLM 后端: {instance.name} (model={config.llm_model})")
        return instance


# 默认 LLM 实例
def get_llm(backend: Optional[str] = None) -> LLMBackend:
    """快捷获取 LLM 实例"""
    return LLMFactory.create(backend)
