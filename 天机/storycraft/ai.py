"""
AI 调用网关 — AIGateway
========================
统一 LLM 调用入口，整合三大核心组件：
  1. PromptWorkshop  → 模板渲染（天机 prompts.py）
  2. ProfileRegistry → 生成配置档案（温度/模型/长度）
  3. LLMFactory      → 多后端 LLM 调用（天机 core/llm.py）

用法:
    gateway = AIGateway()
    result = gateway.generate(
        prompt_name="chapter_write",
        context={"title": "初遇", "chapter": 1, ...},
        profile_name="writing",
    )
    print(result["text"])
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from .prompts import PromptWorkshop, PromptTemplate
from ..core.llm import get_llm, LLMBackend

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 1. 生成配置档案
# ──────────────────────────────────────────────


@dataclass
class GenerationProfile:
    """生成配置档案 — 定义每次 AI 调用的参数"""

    name: str
    model: Optional[str] = None  # None 表示使用 LLMFactory 全局模型
    temperature: float = 0.85
    max_tokens: int = 4096
    top_p: float = 0.95
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.2
    stop_sequences: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        d: dict = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        if self.model:
            d["model"] = self.model
        if self.stop_sequences:
            d["stop"] = self.stop_sequences
        return d


class ProfileRegistry:
    """生成配置档案注册表"""

    def __init__(self):
        self._profiles: dict[str, GenerationProfile] = {}
        self._init_defaults()

    def _init_defaults(self):
        defaults = [
            GenerationProfile(
                name="creative",
                temperature=0.90,
                max_tokens=4096,
                description="创意生成（大纲、角色、世界观）",
            ),
            GenerationProfile(
                name="writing",
                temperature=0.85,
                max_tokens=8192,
                description="章节写作（需要较长输出）",
            ),
            GenerationProfile(
                name="editing",
                temperature=0.65,
                max_tokens=4096,
                description="编辑改写（需要更精确的输出）",
            ),
            GenerationProfile(
                name="analysis",
                temperature=0.30,
                max_tokens=2048,
                description="分析类任务（一致性、节奏分析）",
            ),
            GenerationProfile(
                name="quick",
                temperature=0.70,
                max_tokens=1024,
                description="快速生成（摘要、标签）",
            ),
        ]
        for p in defaults:
            self._profiles[p.name] = p

    def get(self, name: str) -> GenerationProfile:
        if name not in self._profiles:
            raise KeyError(
                f"Profile '{name}' not found. Available: {list(self._profiles.keys())}"
            )
        return self._profiles[name]

    def register(self, profile: GenerationProfile):
        self._profiles[profile.name] = profile

    def list(self) -> list[str]:
        return list(self._profiles.keys())

    def get_default(self) -> GenerationProfile:
        return self._profiles["writing"]


# ──────────────────────────────────────────────
# 2. AI 网关
# ──────────────────────────────────────────────


class AIGateway:
    """
    AI 调用网关

    - 统一 prompt 组装 + 策略配置
    - Retry / fallback
    - Token 用量追踪
    - 底层使用天机 LLMFactory（支持 DeepSeek / OpenAI / Ollama）
    """

    def __init__(self, story_id: str = "default"):
        self.prompts = PromptWorkshop(story_id=story_id)
        self.profiles = ProfileRegistry()
        self.total_tokens_used = 0
        self.total_calls = 0

        # 注册 novel-agent 迁移过来的额外模板
        self._register_novel_templates()

    def _register_novel_templates(self):
        """注册从 novel-agent 迁移的高阶模板（与天机已有模板互补）"""
        extras = [
            PromptTemplate(
                name="outline_generation",
                category="plot",
                template=(
                    "请根据以下概念生成一份完整的故事大纲：\n\n"
                    "【作品概念】\n{concept}\n\n"
                    "【风格要求】\n{style}\n\n"
                    "【目标读者】\n{target_audience}\n\n"
                    "【额外要求】\n{extra_requirements}\n\n"
                    "大纲需包含以下部分：\n"
                    "1. 作品简介（100-200字）\n"
                    "2. 世界观设定概述\n"
                    "3. 主要角色列表（含定位）\n"
                    "4. 分卷结构（每卷3-5章，共4-6卷）\n"
                    "5. 核心爽点与卖点\n"
                    "6. 预计字数规划"
                ),
                description="完整故事大纲生成",
                variables=[
                    "concept",
                    "style",
                    "target_audience",
                    "extra_requirements",
                ],
                tags=["plot", "outline"],
            ),
            PromptTemplate(
                name="chapter_continue",
                category="plot",
                template=(
                    "请续写下一章：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【上一章内容】\n{previous_chapter}\n\n"
                    "【后续发展提示】\n{next_hints}\n\n"
                    "【写作要求】\n"
                    "- 字数：{word_count} 字左右\n"
                    "- 保持与前文一致的风格和节奏\n"
                    "- 本章结尾也需要设置新的悬念"
                ),
                description="章节续写",
                variables=[
                    "novel_title",
                    "previous_chapter",
                    "next_hints",
                    "word_count",
                ],
                tags=["writing", "chapter"],
            ),
            PromptTemplate(
                name="chapter_summary",
                category="general",
                template=(
                    "请对以下章节进行摘要：\n\n"
                    "【章节标题】{chapter_title}\n"
                    "【正文】\n{content}\n\n"
                    "请用 100-200 字概括本章核心剧情。"
                ),
                description="章节摘要生成",
                variables=["chapter_title", "content"],
                tags=["summary"],
            ),
            PromptTemplate(
                name="quality_check",
                category="revise",
                template=(
                    "请对以下章节进行质量检查，从以下维度评分（1-10）：\n\n"
                    "【章节标题】{chapter_title}\n"
                    "【正文】\n{content}\n\n"
                    "评分维度：\n"
                    "1. 文笔流畅度\n"
                    "2. 角色一致性\n"
                    "3. 节奏把控\n"
                    "4. 悬念设置\n"
                    "5. 情节合理性\n\n"
                    "请列出每个维度的评分及简短理由。"
                ),
                description="章节质量检查",
                variables=["chapter_title", "content"],
                tags=["revise", "quality"],
            ),
            PromptTemplate(
                name="character_analysis",
                category="character",
                template=(
                    "请分析以下角色设定的完整性和一致性：\n\n"
                    "【角色名称】{name}\n"
                    "【角色设定】\n{description}\n\n"
                    "【已出场表现】\n{appearances}\n\n"
                    "请分析：\n"
                    "1. 角色设定的完整性（是否缺乏关键信息）\n"
                    "2. 行为一致性（是否有 OOC 表现）\n"
                    "3. 成长弧光（是否有变化轨迹）\n"
                    "4. 改进建议"
                ),
                description="角色设定分析",
                variables=["name", "description", "appearances"],
                tags=["character", "analysis"],
            ),
        ]
        for tmpl in extras:
            self.prompts.register(tmpl)

    # ────────────────────────────────────────
    # 核心方法
    # ────────────────────────────────────────

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
            stream: 是否使用流式输出
            max_retries: 最大重试次数

        Returns:
            dict: {
                "text": str,
                "tokens": int,
                "model": str,
                "latency": float,
                "profile": str,
                "prompt": str,
            }
        """
        # 1. Render prompts (system + user)
        system_prompt = self._build_system(prompt_name, context)
        user_prompt = self.prompts.render(prompt_name, **context)
        if user_prompt is None:
            raise ValueError(
                f"Prompt template '{prompt_name}' not found. "
                f"Available: {list(self.prompts.list_all())}"
            )

        # 2. Get profile
        if profile_name:
            profile = self.profiles.get(profile_name)
        else:
            profile = self._auto_select_profile(prompt_name)

        # 3. 构造消息
        messages = [{"role": "user", "content": user_prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        # 4. Retry 循环
        last_error: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                start = time.time()
                result = self._call_with_profile(messages, profile, stream)
                latency = time.time() - start

                self.total_calls += 1
                self.total_tokens_used += result.get("tokens", 0)

                return {
                    "text": result["text"],
                    "tokens": result.get("tokens", 0),
                    "model": result.get("model", ""),
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

    def _build_system(self, prompt_name: str, context: dict) -> str:
        """根据 prompt 类型构建 system prompt"""
        system_map = {
            "outline": (
                "你是一位资深的网文大纲策划专家，擅长为各类网络小说设计完整、精彩的故事大纲。"
                "你的大纲结构清晰、节奏紧凑、爽点密集，符合当前网文市场的流行趋势。"
                "请严格按照以下格式输出，不要添加额外说明。"
            ),
            "write": (
                "你是一位专业的网文作者，文笔流畅、剧情紧凑、人物鲜活。"
                "你擅长根据大纲和章节概要写出高质量的网文章节。"
                "注意保持合理的章节节奏：开头有小钩子，中间有冲突或爽点，结尾有悬念。"
                "直接输出章节正文，不要添加章节标题以外的说明。"
            ),
            "continue": (
                "你是一位网文续写专家。你将收到前一章的完整内容，请自然地续写出下一章。"
                "保持人物性格、行文风格、叙事节奏的一致性。"
                "续写内容应承接上一章的结尾悬念，顺势展开新的情节。"
                "直接输出新的章节正文。"
            ),
            "rewrite": (
                "你是一位网文编辑，擅长分析并改写章节内容。"
                "你能够在保留原作核心情节的前提下，根据修改意见精准地重写章节。"
                "注意保持人物性格一致性和世界观的统一。"
            ),
            "quality": (
                "你是一位专业的网文质量审核编辑，擅长从多个维度分析章节质量。"
                "请客观评分，指出具体问题并提供改进建议。"
            ),
            "character": ("你是一位角色设计专家，擅长分析角色设定的完整性和一致性。"),
        }
        for key, sp in system_map.items():
            if key in prompt_name.lower():
                return sp
        return ""

    def _call_with_profile(
        self,
        messages: list[dict],
        profile: GenerationProfile,
        stream: bool = False,
    ) -> dict:
        """
        使用 profile 参数调用 LLM。
        临时覆盖 backend 属性以应用 per-call 配置。
        """
        backend: LLMBackend = get_llm()

        # 保存原始值以便恢复
        saved = {}
        overrides = {
            "temperature": profile.temperature,
            "max_tokens": profile.max_tokens,
            "top_p": profile.top_p,
        }
        for attr, val in overrides.items():
            if hasattr(backend, attr):
                saved[attr] = getattr(backend, attr)
                setattr(backend, attr, val)

        try:
            raw_text = backend.chat(messages, stream=stream)
            text = (
                "".join(raw_text)
                if isinstance(raw_text, __import__("typing").Iterator)
                else str(raw_text)
            )  # type: ignore

            # 简单 token 估算
            tokens = (
                backend.count_tokens(text)
                if hasattr(backend, "count_tokens")
                else len(text) // 2
            )

            return {
                "text": text,
                "tokens": tokens,
                "model": getattr(backend, "model", ""),
            }
        finally:
            # 恢复原始值
            for attr, val in saved.items():
                setattr(backend, attr, val)

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
            "summary": "quick",
            "quality": "analysis",
        }
        for key, profile_name in mapping.items():
            if key in prompt_name.lower():
                return self.profiles.get(profile_name)
        return self.profiles.get_default()

    def get_stats(self) -> dict:
        """获取调用统计"""
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens_used,
        }
