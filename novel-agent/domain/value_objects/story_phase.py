"""
故事阶段值对象 - 描述故事当前所处的叙事阶段
"""

from enum import Enum
from typing import Optional


class StoryPhase(Enum):
    """叙事阶段枚举 - 基于经典故事结构分析"""

    CONCEPT = "concept"  # 概念构思
    SETUP = "setup"  # 设定展开
    INCITING_INCIDENT = "inciting_incident"  # 激励事件
    RISING_ACTION = "rising_action"  # 上升行动
    MIDPOINT = "midpoint"  # 中点转折
    CRISIS = "crisis"  # 危机
    CLIMAX = "climax"  # 高潮
    FALLING_ACTION = "falling_action"  # 下降行动
    RESOLUTION = "resolution"  # 结局
    EPILOGUE = "epilogue"  # 尾声

    def description(self) -> str:
        """获取阶段的中文描述"""
        descriptions = {
            StoryPhase.CONCEPT: "故事概念构思阶段",
            StoryPhase.SETUP: "世界观和角色设定展开",
            StoryPhase.INCITING_INCIDENT: "打破平衡的激励事件发生",
            StoryPhase.RISING_ACTION: "冲突升级，剧情推进",
            StoryPhase.MIDPOINT: "故事中点，重大转折或 revelation",
            StoryPhase.CRISIS: "最大危机出现，主角面临选择",
            StoryPhase.CLIMAX: "最终对决，故事高潮",
            StoryPhase.FALLING_ACTION: "高潮后的余波",
            StoryPhase.RESOLUTION: "故事收束，揭示结局",
            StoryPhase.EPILOGUE: "尾声，交代后续",
        }
        return descriptions.get(self, "未知阶段")

    def is_early_stage(self) -> bool:
        return self in (
            StoryPhase.CONCEPT,
            StoryPhase.SETUP,
            StoryPhase.INCITING_INCIDENT,
        )

    def is_mid_stage(self) -> bool:
        return self in (
            StoryPhase.RISING_ACTION,
            StoryPhase.MIDPOINT,
            StoryPhase.CRISIS,
        )

    def is_late_stage(self) -> bool:
        return self in (
            StoryPhase.CLIMAX,
            StoryPhase.FALLING_ACTION,
            StoryPhase.RESOLUTION,
            StoryPhase.EPILOGUE,
        )


class WritingPhase(Enum):
    """写作生产阶段枚举"""

    BRAINSTORMING = "brainstorming"  # 头脑风暴
    OUTLINING = "outlining"  # 大纲编写
    FIRST_DRAFT = "first_draft"  # 初稿
    REVISION = "revision"  # 修订
    POLISHING = "polishing"  # 润色
    COMPLETED = "completed"  # 完成

    def description(self) -> str:
        desc = {
            WritingPhase.BRAINSTORMING: "创意构思与头脑风暴",
            WritingPhase.OUTLINING: "故事大纲与结构设计",
            WritingPhase.FIRST_DRAFT: "第一稿写作",
            WritingPhase.REVISION: "内容修订与重写",
            WritingPhase.POLISHING: "细节润色与打磨",
            WritingPhase.COMPLETED: "作品完成",
        }
        return desc.get(self, "")
