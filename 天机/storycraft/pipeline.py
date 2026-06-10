"""
十步写作管线 — Story Pipeline
================================
模块化、可插拔、数据流驱动的创作管线。
灵感源于经典编剧理论（英雄之旅 / Save the Cat / 起承转合四幕结构）。

十步流程:
  1. Plan       — 规划：分析用户输入，生成创作蓝图
  2. Bible      — 设定：初始化角色/世界观/设定库
  3. Outline    — 大纲：按四幕结构输出分章大纲
  4. State      — 状态机：注册伏笔、设定叙事阶段
  5. Write      — 写作：逐章生成正文
  6. Quality    — 质检：六维质量评分
  7. Revise     — 修改：根据质检报告优化
  8. Memorize   — 记忆化：存储章节关键记忆
  9. Recall     — 召回：检索跨章节上下文
  10. Polish    — 润色：最终润色 + 格式标准化

每个步骤都是一个独立的可调函数 (StepFunc)。
通过 PipelineContext 传递数据。
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from .state_machine import NarrativeStateMachine, NarrativePhase
from .bible import StoryBible
from .quality import QualityEngine, QualityReport
from .prompts import PromptWorkshop
from .memory import NarrativeMemory


# ── 管线上下文 ────────────────────────────────────────


@dataclass
class PipelineContext:
    """十步管线的共享上下文，每个步骤读/写此对象"""

    # 基础信息
    story_id: str = ""
    title: str = ""
    genre: str = ""
    style: str = ""

    # 用户原始输入
    user_input: str = ""
    requirements: str = ""

    # 各步骤产出
    plan: dict = field(default_factory=dict)
    outline: list[dict] = field(
        default_factory=list
    )  # [{chapter, title, summary, phase}, ...]
    chapters: list[str] = field(default_factory=list)  # 正文列表
    current_chapter: int = 0

    # 子模块实例（由 Pipeline 注入）
    state_machine: Optional[NarrativeStateMachine] = None
    bible: Optional[StoryBible] = None
    quality: Optional[QualityEngine] = None
    prompts: Optional[PromptWorkshop] = None
    memory: Optional[NarrativeMemory] = None

    # 质检报告（按章节索引）
    quality_reports: dict[int, QualityReport] = field(default_factory=dict)

    # 修订历史
    revision_history: list[dict] = field(default_factory=list)

    # 管线状态
    current_step: str = ""
    step_results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "title": self.title,
            "genre": self.genre,
            "style": self.style,
            "plan": self.plan,
            "outline": self.outline,
            "chapter_count": len(self.chapters),
            "current_chapter": self.current_chapter,
            "current_step": self.current_step,
            "quality_reports": {
                str(k): v.to_dict() for k, v in self.quality_reports.items()
            },
            "errors": self.errors,
            "elapsed": round(time.time() - self.started_at, 2),
        }

    def summary(self) -> str:
        lines = [f"📋 管线状态 | {self.title or '未命名'}"]
        lines.append(f"   当前步骤: {self.current_step or '未启动'}")
        lines.append(f"   类型/风格: {self.genre} / {self.style}")
        lines.append(f"   已完成章节: {len(self.chapters)}")
        lines.append(f"   错误数: {len(self.errors)}")
        lines.append(f"   耗时: {round(time.time() - self.started_at, 1)}s")
        return "\n".join(lines)


# ── 步骤类型 ──────────────────────────────────────────

StepFunc = Callable[[PipelineContext], PipelineContext]


# ── 十步管线引擎 ──────────────────────────────────────


class StoryPipeline:
    """
    十步写作管线引擎

    用法:
        pipeline = StoryPipeline()
        pipeline.set_step("plan", my_plan_step)
        ctx = PipelineContext(title="我的小说", genre="仙侠")
        result = pipeline.run(ctx)
        print(result.chapters)
    """

    STEPS = [
        "plan",
        "bible",
        "outline",
        "state",
        "write",
        "quality",
        "revise",
        "memorize",
        "recall",
        "polish",
    ]

    STEP_LABELS = {
        "plan": "1/10 📐 规划",
        "bible": "2/10 📖 设定",
        "outline": "3/10 🗺️ 大纲",
        "state": "4/10 ⚙️ 状态机",
        "write": "5/10 ✍️ 写作",
        "quality": "6/10 🔍 质检",
        "revise": "7/10 🔧 修改",
        "memorize": "8/10 🧠 记忆化",
        "recall": "9/10 🔄 召回",
        "polish": "10/10 ✨ 润色",
    }

    def __init__(self):
        self._steps: dict[str, StepFunc] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """注册内置默认步骤实现"""
        self.set_step("plan", step_plan)
        self.set_step("bible", step_bible)
        self.set_step("outline", step_outline)
        self.set_step("state", step_state)
        self.set_step("write", step_write)
        self.set_step("quality", step_quality)
        self.set_step("revise", step_revise)
        self.set_step("memorize", step_memorize)
        self.set_step("recall", step_recall)
        self.set_step("polish", step_polish)

    def set_step(self, name: str, func: StepFunc) -> None:
        """注册/替换某个步骤"""
        if name not in self.STEPS:
            raise ValueError(f"未知步骤: {name}，可选: {', '.join(self.STEPS)}")
        self._steps[name] = func

    def get_step(self, name: str) -> Optional[StepFunc]:
        return self._steps.get(name)

    def run(
        self,
        ctx: PipelineContext,
        start_step: str = "plan",
        end_step: str = "polish",
        steps_override: Optional[list[str]] = None,
    ) -> PipelineContext:
        """
        执行管线

        参数:
            ctx:            管线上下文
            start_step:     起始步骤
            end_step:       结束步骤
            steps_override: 自定义步骤序列（覆盖默认十步）

        返回:
            执行完成的 PipelineContext
        """
        step_sequence = steps_override or self.STEPS

        # 确定起始/结束索引
        try:
            start_idx = step_sequence.index(start_step)
            end_idx = step_sequence.index(end_step) + 1
        except ValueError as e:
            ctx.errors.append(f"步骤名称错误: {e}")
            return ctx

        # 初始化子模块（如果未被外部注入）
        self._ensure_modules(ctx)

        for step_name in step_sequence[start_idx:end_idx]:
            step_func = self._steps.get(step_name)
            if step_func is None:
                ctx.errors.append(f"步骤 '{step_name}' 未注册，跳过")
                continue

            ctx.current_step = step_name
            label = self.STEP_LABELS.get(step_name, step_name)
            print(f"  [{label}] ...")

            try:
                ctx = step_func(ctx)
                ctx.step_results[step_name] = {"status": "ok", "time": time.time()}
            except Exception as e:
                err_msg = f"[{step_name}] 错误: {e}\n{traceback.format_exc()}"
                ctx.errors.append(err_msg)
                ctx.step_results[step_name] = {"status": "error", "error": str(e)}
                print(f"  ⛔ {err_msg}")
                # 步骤失败不中断管线（可继续后续步骤）
                continue

        ctx.current_step = "done"
        return ctx

    def _ensure_modules(self, ctx: PipelineContext) -> None:
        """确保子模块已初始化"""
        if ctx.state_machine is None:
            ctx.state_machine = NarrativeStateMachine(story_id=ctx.story_id)
        if ctx.bible is None:
            ctx.bible = StoryBible(story_id=ctx.story_id)
        if ctx.quality is None:
            ctx.quality = QualityEngine()
        if ctx.prompts is None:
            ctx.prompts = PromptWorkshop(story_id=ctx.story_id)
        if ctx.memory is None:
            ctx.memory = NarrativeMemory()

    def run_single_step(self, ctx: PipelineContext, step_name: str) -> PipelineContext:
        """仅执行单个步骤（用于独立调试/手动触发）"""
        return self.run(ctx, start_step=step_name, end_step=step_name)


# ═══════════════════════════════════════════════════════
# 默认步骤实现
# ═══════════════════════════════════════════════════════


def step_plan(ctx: PipelineContext) -> PipelineContext:
    """
    Step 1: 规划
    分析用户输入，生成创作蓝图
    """
    if not ctx.title and ctx.user_input:
        ctx.title = ctx.user_input.strip()[:50]

    # 保留预先设定的 total_chapters（如用户在调用前手动设置）
    existing_total = 0
    if ctx.plan and "total_chapters" in ctx.plan:
        existing_total = ctx.plan["total_chapters"]

    ctx.plan = {
        "title": ctx.title,
        "genre": ctx.genre,
        "style": ctx.style,
        "total_chapters": existing_total,
        "analysis": f"基于输入：{ctx.user_input[:100]}" if ctx.user_input else "无输入",
        "created_at": time.time(),
    }
    return ctx


def step_bible(ctx: PipelineContext) -> PipelineContext:
    """
    Step 2: 设定
    初始化世界观和角色档案
    """
    bible = ctx.bible
    if bible is None:
        return ctx

    # 如果 bible 尚未设定，写入默认占位
    if not bible.global_notes:
        bible.global_notes = (
            f"标题: {ctx.title} | 类型: {ctx.genre} | 风格: {ctx.style}"
        )
        bible.settings["创作说明"] = ctx.requirements or "自由创作"

    return ctx


def step_outline(ctx: PipelineContext) -> PipelineContext:
    """
    Step 3: 大纲
    按四幕结构产出分章大纲
    """
    total_ch = ctx.plan.get("total_chapters", 10)
    if total_ch <= 0:
        total_ch = 10

    # 四幕分配
    act_ratios = {"opening": 0.25, "development": 0.35, "climax": 0.25, "finale": 0.15}
    n1 = max(1, int(total_ch * act_ratios["opening"]))
    n2 = max(1, int(total_ch * act_ratios["development"]))
    n3 = max(1, int(total_ch * act_ratios["climax"]))
    n4 = total_ch - n1 - n2 - n3

    acts = [
        (1, n1, NarrativePhase.OPENING, "起：建立世界与引入冲突"),
        (n1 + 1, n1 + n2, NarrativePhase.DEVELOPMENT, "承：深化矛盾与发展关系"),
        (
            n1 + n2 + 1,
            n1 + n2 + n3,
            NarrativePhase.CONVERGENCE,
            "转：高潮转折与伏笔收束",
        ),
        (n1 + n2 + n3 + 1, total_ch, NarrativePhase.FINALE, "合：终极对决与结局"),
    ]

    ctx.outline = []
    for start, end, phase, desc in acts:
        for ch in range(start, end + 1):
            ctx.outline.append(
                {
                    "chapter": ch,
                    "phase": phase.value,
                    "act_description": desc,
                    "title": f"第{ch}章",
                    "summary": "",
                }
            )

    return ctx


def step_state(ctx: PipelineContext) -> PipelineContext:
    """
    Step 4: 状态机
    注册核心伏笔、设置叙事阶段
    """
    sm = ctx.state_machine
    if sm is None:
        return ctx

    # 仅当没有大纲时注册占位伏笔
    if not sm.hooks:
        sm.plant_hook(
            hook_id="核心冲突",
            description=f"《{ctx.title}》的核心矛盾",
            chapter=max(len(ctx.outline), 1),
            category="plot",
        )

    # 根据大纲设定阶段
    for item in ctx.outline:
        sm.set_current_chapter(item["chapter"])

    return ctx


def step_write(ctx: PipelineContext) -> PipelineContext:
    """
    Step 5: 写作
    逐章生成正文（离线模式下生成占位章节）
    """
    if not ctx.outline:
        # 用 plan 中的 total_chapters（如果有）生成完整大纲，让断点续写也能继续工作
        total_ch = ctx.plan.get("total_chapters", 1)
        ctx.outline = [
            {"chapter": ch, "phase": "opening", "title": f"第{ch}章", "summary": ""}
            for ch in range(1, total_ch + 1)
        ]

    # 生成每一章
    for item in ctx.outline:
        ch = item["chapter"]
        if ch <= len(ctx.chapters):
            continue  # 已存在则跳过

        chapter_text = _generate_placeholder_chapter(ctx, item)
        ctx.chapters.append(chapter_text)
        ctx.current_chapter = ch

        # 状态机推进
        if ctx.state_machine:
            ctx.state_machine.set_current_chapter(ch)

    return ctx


def _generate_placeholder_chapter(ctx: PipelineContext, item: dict) -> str:
    """生成占位章节（离线模式；对接 LLM 后替换）"""
    ch = item["chapter"]
    phase_label = item.get("phase", "opening")
    title = item.get("title", f"第{ch}章")

    lines = [
        f"# {title}",
        f"",
        f"叙事阶段：{phase_label}",
        f"风格：{ctx.style or '通用'}",
        f"",
        f"（本章为自动生成占位内容，待对接 LLM 后替换）",
        f"",
    ]

    # 从 bible 获取角色信息
    if ctx.bible and ctx.bible.characters:
        for name, profile in list(ctx.bible.characters.items())[:2]:
            lines.append(f"[{name}] — {profile.name or '主要角色'}")

    lines.append("")
    lines.append(f"第{ch}章正文内容。")
    lines.append("")

    # 从 memory 检索上下文
    if ctx.memory and ctx.memory.count() > 0:
        context = ctx.memory.recall_context(title, window=3)
        lines.append(f"<!-- 记忆上下文:\n{context}\n-->")

    return "\n".join(lines)


def step_quality(ctx: PipelineContext) -> PipelineContext:
    """
    Step 6: 质检
    对所有已生成的章节执行六维质量评分
    """
    quality = ctx.quality
    if quality is None:
        return ctx

    for i, chapter_text in enumerate(ctx.chapters):
        ch_num = i + 1
        if ch_num in ctx.quality_reports:
            continue  # 已质检过则跳过

        report = quality.evaluate(chapter_text, title=f"第{ch_num}章")
        ctx.quality_reports[ch_num] = report

    return ctx


def step_revise(ctx: PipelineContext) -> PipelineContext:
    """
    Step 7: 修改
    根据质检报告优化未通过的章节
    """
    for ch_num, report in ctx.quality_reports.items():
        if report.passed:
            continue

        idx = ch_num - 1
        if idx < 0 or idx >= len(ctx.chapters):
            continue

        original = ctx.chapters[idx]
        issues = []
        for d in report.dimensions.values():
            if not d.passed:
                issues.extend(d.suggestions[:2])

        if issues:
            # 修改记录
            ctx.revision_history.append(
                {
                    "chapter": ch_num,
                    "original_length": len(original),
                    "issues": issues,
                    "revised_at": time.time(),
                }
            )

    return ctx


def step_memorize(ctx: PipelineContext) -> PipelineContext:
    """
    Step 8: 记忆化
    将章节关键信息存储到叙事记忆
    """
    memory = ctx.memory
    if memory is None:
        return ctx

    for i, chapter_text in enumerate(ctx.chapters):
        ch_num = i + 1
        # 提取前200字作为记忆内容
        content = chapter_text[:200].strip()
        if content:
            memory.store(
                memory_type="plot",
                content=f"第{ch_num}章: {content[:100]}",
                keywords=f"第{ch_num}章,{ctx.title}",
                chapter=ch_num,
                importance=7,
            )

    return ctx


def step_recall(ctx: PipelineContext) -> PipelineContext:
    """
    Step 9: 召回
    检索跨章节一致性上下文（增强后续写作的连贯性）
    """
    memory = ctx.memory
    if memory is None or memory.count() == 0:
        return ctx

    # 收集所有章节的上下文摘要到 step_results
    context_summaries = {}
    for i in range(len(ctx.chapters)):
        ch_num = i + 1
        summary = memory.recall_context(f"第{ch_num}章", window=2)
        context_summaries[ch_num] = summary

    ctx.step_results["recall_context"] = context_summaries
    return ctx


def step_polish(ctx: PipelineContext) -> PipelineContext:
    """
    Step 10: 润色
    最终格式标准化 + 章节编号校验
    """
    polished = []
    for i, chapter_text in enumerate(ctx.chapters):
        ch_num = i + 1
        lines = chapter_text.split("\n")

        # 确保标题格式统一
        has_title = any(
            line.strip().startswith("# ") or line.strip().startswith(f"# 第{ch_num}章")
            for line in lines
        )
        if not has_title:
            lines.insert(0, f"# 第{ch_num}章")
            lines.insert(1, "")

        # 去除过长的空行序列
        cleaned = []
        empty_count = 0
        for line in lines:
            if line.strip() == "":
                empty_count += 1
                if empty_count <= 2:
                    cleaned.append(line)
            else:
                empty_count = 0
                cleaned.append(line)

        polished.append("\n".join(cleaned))

    ctx.chapters = polished
    return ctx
