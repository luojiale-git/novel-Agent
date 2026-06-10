"""
提示词工坊 — Prompt Workshop
==============================
轻量模板引擎 + 变量注入 + 版本追踪。

核心功能：
  - 命名模板注册（分类管理）
  - Python str.format() 变量注入（零外部依赖）
  - 模板版本控制
  - 组合模板（subprompts 拼接）
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PromptTemplate:
    """提示词模板"""

    name: str
    category: str = "general"  # general | character | plot | world | style | revise
    template: str = ""
    description: str = ""
    variables: list[str] = field(default_factory=list)  # 模板中用到的变量名
    version: int = 1
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def render(self, **kwargs) -> str:
        """
        注入变量生成最终提示词

        用法:
            tmpl.render(character="林夜", scene="雨夜追捕")
        """
        # 检查缺失变量
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            # 缺失变量用占位符替代
            for m in missing:
                kwargs.setdefault(m, f"{{{m}}}")
        return self.template.format(**kwargs)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "template": self.template,
            "description": self.description,
            "variables": self.variables,
            "version": self.version,
            "tags": self.tags,
        }


class PromptWorkshop:
    """
    提示词工坊 — 管理所有叙事提示词模板

    用法:
        pw = PromptWorkshop()
        pw.register(PromptTemplate(
            name="chapter_write",
            category="plot",
            template="请写第{chapter}章「{title}」\n背景：{context}\n风格：{style}",
            variables=["chapter", "title", "context", "style"],
        ))
        prompt = pw.render("chapter_write", chapter=5, title="雨夜", context="...", style="悬疑")
    """

    def __init__(self, story_id: str = "default"):
        self.story_id = story_id
        self._templates: dict[str, PromptTemplate] = {}
        self._categories: dict[str, list[str]] = {}  # category -> [template_names]
        self._register_defaults()

    def _register_defaults(self) -> None:
        """注册默认内置模板"""
        defaults = [
            PromptTemplate(
                name="chapter_write",
                category="plot",
                template=(
                    "请创作第 {chapter} 章\n"
                    "标题：{title}\n"
                    "叙事阶段：{phase}\n"
                    "当前世界观概要：{world_summary}\n"
                    "本章重点角色：{characters}\n"
                    "剧情上下文：{context}\n"
                    "写作要求：\n"
                    "1. 保持 {style} 风格\n"
                    "2. 推进伏笔：{hooks}\n"
                    "3. 字数约 {word_count} 字\n"
                    "4. 注意角色一致性（OOC 检测）\n"
                    "5. 章节结尾要有钩子或收束感\n"
                    "开始写作："
                ),
                description="标准章节生成模板",
                variables=[
                    "chapter",
                    "title",
                    "phase",
                    "world_summary",
                    "characters",
                    "context",
                    "style",
                    "hooks",
                    "word_count",
                ],
                tags=["writing", "chapter"],
            ),
            PromptTemplate(
                name="character_dialogue",
                category="character",
                template=(
                    "角色名：{name}\n"
                    "角色身份：{role}\n"
                    "性格概要：{personality}\n"
                    "当前状态：{current_state}\n"
                    "对话对象：{target}\n"
                    "对话场景：{scene}\n"
                    "对话目标：{goal}\n\n"
                    "请根据以上角色设定，写出符合角色性格的对话。要求：\n"
                    "1. 语气、用词符合角色身份\n"
                    "2. 体现当前情绪状态\n"
                    "3. 推动剧情或揭示信息\n"
                    "对话内容："
                ),
                description="角色对话生成",
                variables=[
                    "name",
                    "role",
                    "personality",
                    "current_state",
                    "target",
                    "scene",
                    "goal",
                ],
                tags=["character", "dialogue"],
            ),
            PromptTemplate(
                name="revise_chapter",
                category="revise",
                template=(
                    "请修改以下文本。\n\n"
                    "质量检测报告：\n{quality_report}\n\n"
                    "原文：\n{text}\n\n"
                    "修改要求：\n{requirements}\n"
                    "请在保留原作风格的前提下修正上述问题。修改结果："
                ),
                description="根据质量报告修改章节",
                variables=["quality_report", "text", "requirements"],
                tags=["revise", "quality"],
            ),
            PromptTemplate(
                name="world_setting",
                category="world",
                template=(
                    "世界观名称：{world_name}\n"
                    "类型：{genre}\n"
                    "核心设定：{core_setting}\n"
                    "特殊规则：{rules}\n\n"
                    "请详细描述该世界观下的：\n"
                    "1. 物理/魔法规则\n"
                    "2. 社会结构\n"
                    "3. 主要势力\n"
                    "4. 日常生活的典型样貌\n"
                    "5. 冲突根源\n\n"
                    "描述："
                ),
                description="世界观设定生成",
                variables=["world_name", "genre", "core_setting", "rules"],
                tags=["world", "setting"],
            ),
            PromptTemplate(
                name="plot_outline",
                category="plot",
                template=(
                    "请根据以下信息生成剧情大纲：\n\n"
                    "世界观：{world}\n"
                    "主角：{protagonist}\n"
                    "核心冲突：{conflict}\n"
                    "预计篇幅：{total_chapters} 章\n"
                    "风格倾向：{style}\n\n"
                    "请按四幕结构（起承转合）输出分章大纲：\n"
                    "起（第1~{opening_end}章）：建立世界，引入冲突\n"
                    "承（第{dev_start}~{dev_end}章）：深化矛盾，发展关系\n"
                    "转（第{conv_start}~{conv_end}章）：高潮转折，收束线索\n"
                    "合（第{finale_start}~{total_chapters}章）：终极对决，结局\n"
                ),
                description="剧情大纲生成",
                variables=[
                    "world",
                    "protagonist",
                    "conflict",
                    "total_chapters",
                    "style",
                    "opening_end",
                    "dev_start",
                    "dev_end",
                    "conv_start",
                    "conv_end",
                    "finale_start",
                ],
                tags=["plot", "outline"],
            ),
        ]
        for tmpl in defaults:
            self.register(tmpl)

    def register(self, template: PromptTemplate) -> PromptTemplate:
        """注册模板"""
        self._templates[template.name] = template
        cat = template.category
        if cat not in self._categories:
            self._categories[cat] = []
        if template.name not in self._categories[cat]:
            self._categories[cat].append(template.name)
        return template

    def get(self, name: str) -> Optional[PromptTemplate]:
        return self._templates.get(name)

    def render(self, name: str, **kwargs) -> Optional[str]:
        """渲染指定模板"""
        tmpl = self.get(name)
        if tmpl is None:
            return None
        return tmpl.render(**kwargs)

    def list_by_category(self, category: str) -> list[PromptTemplate]:
        """按分类列出模板"""
        names = self._categories.get(category, [])
        return [self._templates[n] for n in names if n in self._templates]

    def list_all(self) -> list[PromptTemplate]:
        return list(self._templates.values())

    def remove(self, name: str) -> bool:
        """移除模板"""
        tmpl = self._templates.pop(name, None)
        if tmpl:
            cat_list = self._categories.get(tmpl.category, [])
            if name in cat_list:
                cat_list.remove(name)
            return True
        return False

    def compose(
        self,
        main_template: str,
        subprompts: list[str],
        separator: str = "\n\n---\n\n",
        **kwargs,
    ) -> Optional[str]:
        """
        组合模板：渲染主模板 + 多个子提示，拼接输出

        subprompts: 子模板名称列表，依次渲染后用 separator 拼接
        kwargs: 传递给所有模板的公共变量
        """
        main = self.render(main_template, **kwargs)
        if main is None:
            return None
        parts = [main]
        for sp_name in subprompts:
            sp = self.render(sp_name, **kwargs)
            if sp:
                parts.append(sp)
        return separator.join(parts)

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "templates": {n: t.to_dict() for n, t in self._templates.items()},
            "categories": dict(self._categories),
        }

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str) -> "PromptWorkshop":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        pw = cls(data.get("story_id", "default"))
        # 清除默认模板，用存储的替换
        pw._templates = {}
        pw._categories = {}
        for tmpl_data in data.get("templates", {}).values():
            pw.register(PromptTemplate(**tmpl_data))
        return pw
