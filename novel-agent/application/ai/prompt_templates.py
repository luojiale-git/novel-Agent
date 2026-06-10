"""
提示词模板注册表 - 管理所有 AI 调用所需的提示词模板
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PromptTemplate:
    """提示词模板数据类"""

    name: str
    system_prompt: str
    user_template: str
    expected_output: str
    version: int = 1


class PromptRegistry:
    """提示词模板注册表 - 统一管理模板的注册、查询、渲染"""

    def __init__(self):
        self._templates: dict[str, PromptTemplate] = {}
        self._init_defaults()

    def _init_defaults(self):
        """注册所有内置模板"""
        defaults = [
            # ──────────────────────────────────────────────
            # 1. 大纲生成
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="outline_generation",
                system_prompt=(
                    "你是一位资深的网文大纲策划专家，擅长为各类网络小说设计完整、精彩的故事大纲。"
                    "你的大纲结构清晰、节奏紧凑、爽点密集，符合当前网文市场的流行趋势。"
                    "请严格按照以下格式输出，不要添加额外说明。"
                ),
                user_template=(
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
                expected_output="完整的故事大纲，包含简介、世界观、角色、分卷结构、爽点、字数规划",
            ),
            # ──────────────────────────────────────────────
            # 2. 章节写作
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="chapter_write",
                system_prompt=(
                    "你是一位专业的网文作者，文笔流畅、剧情紧凑、人物鲜活。"
                    "你擅长根据大纲和章节概要写出高质量的网文章节。"
                    "注意保持合理的章节节奏：开头有小钩子，中间有冲突或爽点，结尾有悬念。"
                    "直接输出章节正文，不要添加章节标题以外的说明。"
                ),
                user_template=(
                    "请根据以下信息写出完整的章节内容：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【当前卷名】{volume_title}\n"
                    "【章节概要】\n{chapter_summary}\n\n"
                    "【前情提要】\n{previous_context}\n\n"
                    "【世界观设定】\n{world_settings}\n\n"
                    "【可用角色】\n{characters}\n\n"
                    "【写作要求】\n"
                    "- 字数：{word_count} 字左右\n"
                    "- 视角：{pov}\n"
                    "- 风格：{style}\n"
                    "- 结尾需设置悬念或钩子"
                ),
                expected_output="完整的一章正文，约指定字数，带有章节标题",
            ),
            # ──────────────────────────────────────────────
            # 3. 续写章节
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="chapter_continue",
                system_prompt=(
                    "你是一位网文续写专家。你将收到前一章的完整内容，请自然地续写出下一章。"
                    "保持人物性格、行文风格、叙事节奏的一致性。"
                    "续写内容应承接上一章的结尾悬念，顺势展开新的情节。"
                    "直接输出新的章节正文。"
                ),
                user_template=(
                    "请续写下一章：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【上一章内容】\n{previous_chapter}\n\n"
                    "【后续发展提示】\n{next_hints}\n\n"
                    "【写作要求】\n"
                    "- 字数：{word_count} 字左右\n"
                    "- 保持与前文一致的风格和节奏\n"
                    "- 本章结尾也需要设置新的悬念"
                ),
                expected_output="续写的新章节正文，承接上一章内容",
            ),
            # ──────────────────────────────────────────────
            # 4. 章节改写
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="chapter_rewrite",
                system_prompt=(
                    "你是一位网文编辑，擅长分析并改写章节内容。"
                    "你能够在保留原作核心情节的前提下，根据修改意见精准地重写章节。"
                    "注意保持人物性格一致性和世界观的统一。"
                ),
                user_template=(
                    "请根据修改意见重写以下章节：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【当前章节标题】{chapter_title}\n"
                    "【原章节内容】\n{original_content}\n\n"
                    "【修改意见】\n{revision_instructions}\n\n"
                    "【额外要求】\n{extra_notes}\n\n"
                    "请输出完整的重写后章节。"
                ),
                expected_output="完全重写后的新章节正文",
            ),
            # ──────────────────────────────────────────────
            # 5. 章节扩写
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="chapter_expand",
                system_prompt=(
                    "你是一位擅长细节描写的网文作者。你能够在原有章节的基础上增加细节描写、"
                    "心理活动、对话互动和环境渲染，使章节更加丰满生动。"
                    "扩写时注意不改变原有剧情走向和章节结构。"
                ),
                user_template=(
                    "请扩写以下章节，使内容更加丰富：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【章节标题】{chapter_title}\n"
                    "【原章节内容】\n{original_content}\n\n"
                    "【扩写重点】\n{expand_focus}\n\n"
                    "【目标字数】{target_word_count} 字\n"
                    "【当前字数】{current_word_count} 字\n\n"
                    "请输出扩写后的完整章节。"
                ),
                expected_output="扩写后的完整章节，比原内容更详细、字数更多",
            ),
            # ──────────────────────────────────────────────
            # 6. 角色创建
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="character_creation",
                system_prompt=(
                    "你是一位网文角色设计专家。你擅长创造有血有肉、令人印象深刻的角色。"
                    "每个角色应有清晰的定位、鲜明的性格、合理的背景故事和成长弧线。"
                    "请严格按照指定格式输出角色档案。"
                ),
                user_template=(
                    "请根据以下设定创建一个完整的角色档案：\n\n"
                    "【作品世界观】\n{world_setting}\n\n"
                    "【角色定位】\n{role_position}\n\n"
                    "【角色原型参考】\n{archetype_reference}\n\n"
                    "【与其他角色的关系】\n{relationships}\n\n"
                    "【特殊要求】\n{special_requirements}\n\n"
                    "角色档案需包含：\n"
                    "1. 姓名（含可能的绰号/别名）\n"
                    "2. 基础信息（年龄、性别、外貌、身份）\n"
                    "3. 性格特征（优点、缺点、怪癖）\n"
                    "4. 背景故事\n"
                    "5. 能力/实力体系\n"
                    "6. 动机与目标\n"
                    "7. 成长弧线（初登场→中期→结局）\n"
                    "8. 经典台词（2-3句）"
                ),
                expected_output="完整的角色档案，包含基础信息、性格、背景、能力、成长弧线等",
            ),
            # ──────────────────────────────────────────────
            # 7. 世界观构建
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="world_building",
                system_prompt=(
                    "你是一位网文世界观构建专家。你擅长为网络小说设计逻辑自洽、富有想象力的世界观。"
                    "你的设定既有新意又有深度，能够为故事提供坚实的舞台。"
                    "每个维度请给出详细且有条理的设定说明。"
                ),
                user_template=(
                    "请为以下作品构建世界观内容：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【作品基调】{tone}\n"
                    "【已有设定】\n{existing_settings}\n\n"
                    "【构建维度】{dimension}\n"
                    "（可选维度：力量体系 | 社会结构 | 地理环境 | 历史沿革 | 文化风俗）\n\n"
                    "【详细要求】\n{requirements}\n\n"
                    "请在此维度下给出系统、详细且富有创意的设定，注意与其他维度的兼容性。"
                ),
                expected_output="指定维度的世界观设定内容，详细且有逻辑性",
            ),
            # ──────────────────────────────────────────────
            # 8. 知识抽取
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="knowledge_extraction",
                system_prompt=(
                    "你是一位知识图谱构建专家。请从给定的文本中提取关键实体、关系和事件，"
                    "以 (头实体, 关系, 尾实体) 的三元组形式输出。\n"
                    "每个三元组占一行，格式为：实体1 | 关系 | 实体2\n"
                    "只输出三元组，不要添加任何说明文字。"
                ),
                user_template=(
                    "请从以下文本中提取知识三元组：\n\n"
                    "{text}\n\n"
                    "【重点关注】\n{focus_areas}\n\n"
                    "【抽取要求】\n"
                    "- 实体类型：人物、地点、组织、物品、能力、事件\n"
                    "- 关系类型：所属、拥有、位于、参与、创建、击败、加入等\n"
                    "- 尽量提取有叙事价值的三元组"
                ),
                expected_output="每行一个三元组，格式：实体1 | 关系 | 实体2",
            ),
            # ──────────────────────────────────────────────
            # 9. 故事分析
            # ──────────────────────────────────────────────
            PromptTemplate(
                name="story_analysis",
                system_prompt=(
                    "你是一位专业的网文编辑分析师。你擅长从一致性、节奏、人物塑造、"
                    "逻辑合理性等维度对小说内容进行全面的分析评估。"
                    "你的分析客观、精准、有建设性，能够帮助作者改进作品质量。"
                    "请按照指定格式输出分析报告。"
                ),
                user_template=(
                    "请对以下小说内容进行全面分析：\n\n"
                    "【作品名称】{novel_title}\n"
                    "【待分析内容】\n{content}\n\n"
                    "【分析维度】\n{analysis_dimensions}\n\n"
                    "请从以下方面进行分析：\n"
                    "1. 一致性检查（人物性格是否一致、世界观设定是否矛盾、剧情逻辑是否自洽）\n"
                    "2. 节奏分析（章节节奏、爽点密度、高潮分布）\n"
                    "3. 人物塑造评估（角色立体度、成长弧线、对话质量）\n"
                    "4. 剧情漏洞检测（时间线矛盾、设定冲突、逻辑硬伤）\n"
                    "5. 改进建议（针对发现的问题给出具体修改建议）\n\n"
                    "每个维度给出评分（1-10分）和详细说明。"
                ),
                expected_output="结构化的分析报告，包含各维度评分、问题说明和改进建议",
            ),
        ]

        for t in defaults:
            self._templates[t.name] = t

    def register(self, template: PromptTemplate):
        """注册自定义模板"""
        self._templates[template.name] = template

    def get(self, name: str) -> PromptTemplate:
        """根据名称获取模板"""
        if name not in self._templates:
            raise KeyError(
                f"Prompt template '{name}' not found. "
                f"Available templates: {list(self._templates.keys())}"
            )
        return self._templates[name]

    def list_templates(self) -> list[str]:
        """获取所有已注册模板的名称列表"""
        return list(self._templates.keys())

    def render(self, name: str, **kwargs) -> tuple[str, str]:
        """渲染指定模板，返回 (system_prompt, user_prompt)"""
        template = self.get(name)
        try:
            user_prompt = template.user_template.format(**kwargs)
        except KeyError as e:
            raise KeyError(
                f"Missing required context variable for template '{name}': {e}. "
                f"Provided keys: {list(kwargs.keys())}"
            ) from e
        return template.system_prompt, user_prompt
