import os
import json
import re
from abc import ABC, abstractmethod
from typing import Iterator, Optional

import requests


class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    @abstractmethod
    def chat(
        self, messages: list[dict], stream: bool = False
    ) -> str | Iterator[str]: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...


class DeepSeekBackend(LLMBackend):
    """DeepSeek API - 从环境变量读取配置"""

    def __init__(self):
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    def chat(self, messages: list[dict], stream: bool = False) -> str | Iterator[str]:
        if not self.api_key:
            raise ValueError("未配置 API Key")
        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        if stream:
            return self._stream(url, headers, payload)
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _stream(self, url: str, headers: dict, payload: dict) -> Iterator[str]:
        resp = requests.post(
            url, headers=headers, json=payload, stream=True, timeout=120
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    d = line[6:]
                    if d == "[DONE]":
                        break
                    try:
                        delta = json.loads(d)["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]
                    except Exception:
                        continue

    def count_tokens(self, text: str) -> int:
        chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
        return int(chinese * 1.5 + (len(text) - chinese) * 0.25) + 4

    @property
    def name(self) -> str:
        return "DeepSeek"


class OpenAIBackend(LLMBackend):
    """兼容 OpenAI 格式的其他服务"""

    def __init__(self):
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    def chat(self, messages: list[dict], stream: bool = False) -> str | Iterator[str]:
        if not self.api_key:
            raise ValueError("未配置 OpenAI API Key")
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }
        if stream:
            return self._stream(url, headers, payload)
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _stream(self, url: str, headers: dict, payload: dict) -> Iterator[str]:
        resp = requests.post(
            url, headers=headers, json=payload, stream=True, timeout=120
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    d = line[6:]
                    if d == "[DONE]":
                        break
                    try:
                        delta = json.loads(d)["choices"][0].get("delta", {})
                        if delta.get("content"):
                            yield delta["content"]
                    except Exception:
                        continue

    def count_tokens(self, text: str) -> int:
        chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
        return int(chinese * 1.5 + (len(text) - chinese) * 0.25) + 4

    @property
    def name(self) -> str:
        return "OpenAI"


def get_llm(backend: Optional[str] = None) -> LLMBackend:
    """获取 LLM 后端实例"""
    backend = backend or os.getenv("LLM_BACKEND", "deepseek").lower()
    if backend == "openai":
        return OpenAIBackend()
    return DeepSeekBackend()
