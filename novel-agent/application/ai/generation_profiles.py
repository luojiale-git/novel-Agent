"""
生成配置档案 - 定义不同任务类型的模型调用参数
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GenerationProfile:
    """生成配置档案 - 定义每次 AI 调用的参数"""

    name: str
    model: str = "deepseek-chat"
    temperature: float = 0.85
    max_tokens: int = 4096
    top_p: float = 0.95
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.2
    stop_sequences: list[str] = field(default_factory=lambda: [])
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stop": self.stop_sequences if self.stop_sequences else None,
        }


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
