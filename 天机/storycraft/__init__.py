"""
StoryCraft - 天机叙事增强引擎

基于经典叙事理论（Campbell 英雄之旅 / Freytag 金字塔 / 起承转合四幕结构）构建的轻量模块化创作辅助套件。

核心模块：
  - state_machine : 叙事状态机（全局收敛沙漏）
  - bible         : 世界观/角色/设定管理器
  - pipeline      : 十步写作管线
  - quality       : 质量守门人六维评分
  - prompts       : 提示词工坊
  - memory        : 叙事记忆（轻量语义检索）
"""

from .state_machine import NarrativeStateMachine, NarrativePhase, PlotHook
from .bible import StoryBible, CharacterProfile, Location
from .pipeline import StoryPipeline, PipelineContext
from .quality import QualityEngine
from .prompts import PromptWorkshop
from .memory import NarrativeMemory

__all__ = [
    "NarrativeStateMachine",
    "NarrativePhase",
    "StoryBible",
    "CharacterProfile",
    "Location",
    "PlotHook",
    "StoryPipeline",
    "PipelineContext",
    "QualityEngine",
    "PromptWorkshop",
    "NarrativeMemory",
]
