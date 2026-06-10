"""
AI 调用网关 - 统一的 LLM 调用入口
"""

import os
import time
import json
import logging
from typing import Optional, Generator, Any
import requests

from .prompt_templates import PromptRegistry
from .generation_profiles import ProfileRegistry, GenerationProfile

logger = logging.getLogger(__name__)


class AIGateway:
    """
    AI 调用网关
    - 统一 prompt 组装 + 策略配置
    - Retry/fallback
    - Token 用量追踪
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        default_model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("NOVEL_API_KEY", "")
        self.api_base = (
            api_base or os.getenv("NOVEL_API_BASE", "https://api.deepseek.com/v1")
        ).rstrip("/")
        self.default_model = default_model or os.getenv("NOVEL_MODEL", "deepseek-chat")
        self.prompts = PromptRegistry()
        self.profiles = ProfileRegistry()
        self.total_tokens_used = 0
        self.total_calls = 0

    def generate(
        self,
        prompt_name: str,
        context: dict,
        profile_name: Optional[str] = None,
        stream: bool = False,
        max_retries: int = 2,
    ) -> dict:
        """统一生成入口

        Args:
            prompt_name: 提示词模板名称
            context: 模板上下文变量字典
            profile_name: 可选的生成配置档案名称，为 None 时自动选择
            stream: 是否使用流式输出（暂未完全实现流式返回）
            max_retries: 最大重试次数

        Returns:
            dict: {
                "text": str,          # 生成文本
                "tokens": int,        # 消耗的 token 数
                "model": str,         # 实际使用的模型
                "latency": float,     # 调用延迟（秒）
                "profile": str,       # 使用的配置档案名称
                "prompt": str,        # 使用的提示词模板名称
            }
        """
        # 1. Render prompts
        system_prompt, user_prompt = self.prompts.render(prompt_name, **context)

        # 2. Get profile
        if profile_name:
            profile = self.profiles.get(profile_name)
        else:
            # Auto-select based on prompt name
            profile = self._auto_select_profile(prompt_name)

        # 3. Build payload
        payload = profile.to_dict()
        payload["messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 4. Call with retry
        last_error: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                start = time.time()
                result = self._call_llm(payload, stream)
                latency = time.time() - start

                self.total_calls += 1
                self.total_tokens_used += result.get("tokens", 0)

                return {
                    "text": result["text"],
                    "tokens": result.get("tokens", 0),
                    "model": payload.get("model", self.default_model),
                    "latency": round(latency, 2),
                    "profile": profile.name,
                    "prompt": prompt_name,
                }
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                if attempt < max_retries:
                    time.sleep(1.5**attempt)

        raise RuntimeError(
            f"AI generation failed after {max_retries + 1} attempts: {last_error}"
        )

    def _call_llm(self, payload: dict, stream: bool = False) -> dict:
        """实际调用 LLM API

        Args:
            payload: 请求 payload（含 messages 和模型参数）
            stream: 是否流式调用

        Returns:
            dict: {"text": str, "tokens": int}
        """
        if not self.api_key:
            return {
                "text": "[演示模式] 请设置 NOVEL_API_KEY 环境变量以启用 AI 生成功能。",
                "tokens": 0,
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json={**payload, "stream": stream},
            timeout=120,
        )
        resp.raise_for_status()

        data = resp.json()
        choice = data["choices"][0]
        text = choice.get("message", {}).get("content", "")

        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0) or usage.get("completion_tokens", 0)

        return {"text": text, "tokens": tokens}

    def _auto_select_profile(self, prompt_name: str) -> GenerationProfile:
        """根据 prompt 名称自动选择配置"""
        mapping = {
            "outline": "creative",
            "character": "creative",
            "world": "creative",
            "write": "writing",
            "continue": "writing",
            "expand": "writing",
            "rewrite": "editing",
            "edit": "editing",
            "analysis": "analysis",
            "extract": "quick",
        }
        for key, profile in mapping.items():
            if key in prompt_name.lower():
                return self.profiles.get(profile)
        return self.profiles.get_default()

    def get_stats(self) -> dict:
        """获取调用统计"""
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens_used,
        }
