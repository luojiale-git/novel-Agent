"""
叙事状态机 — 全局收敛沙漏模型
================================
基于古典叙事四段论（起承转合）的轻量级状态机，内置伏笔注册追踪机制。

阶段模型：起(OPENING) → 承(DEVELOPMENT) → 转(CONVERGENCE) → 合(FINALE)
收敛规则：进度超过 75% 后自动收紧，禁止新伏笔，强制排雷
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional


class NarrativePhase(Enum):
    """叙事四阶段"""

    OPENING = "opening"  # 起: 0-25%
    DEVELOPMENT = "development"  # 承: 25-75%
    CONVERGENCE = "convergence"  # 转: 75-90%
    FINALE = "finale"  # 合: 90-100%

    @classmethod
    def from_progress(cls, progress: float) -> "NarrativePhase":
        """根据进度自动推断当前阶段"""
        if progress < 0.25:
            return cls.OPENING
        elif progress < 0.75:
            return cls.DEVELOPMENT
        elif progress < 0.90:
            return cls.CONVERGENCE
        else:
            return cls.FINALE

    def allows_new_hooks(self) -> bool:
        """是否允许开新伏笔"""
        return self in (self.OPENING, self.DEVELOPMENT)

    def allows_slice_of_life(self) -> bool:
        """是否允许日常/休闲章节"""
        return self in (self.OPENING, self.DEVELOPMENT)

    def requires_hook_resolution(self) -> bool:
        """是否要求伏笔回收率"""
        return self in (self.CONVERGENCE, self.FINALE)

    def tension_multiplier(self) -> float:
        """阶段张力倍率"""
        return {"opening": 0.6, "development": 1.0, "convergence": 1.5, "finale": 2.0}[
            self.value
        ]

    def label_cn(self) -> str:
        return {
            "opening": "起·开局",
            "development": "承·展开",
            "convergence": "转·收敛",
            "finale": "合·终章",
        }[self.value]


@dataclass
class PlotHook:
    """伏笔"""

    id: str
    description: str
    chapter_planted: int
    chapter_resolved: Optional[int] = None
    category: str = "general"  # general | character | item | mystery | relationship
    is_resolved: bool = False
    resolution_note: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChapterRecord:
    """章节记录"""

    number: int
    title: str = ""
    word_count: int = 0
    tension_score: float = 0.0
    summary: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)


class NarrativeStateMachine:
    """
    叙事状态机 — 全局收敛沙漏

    用法:
        nsm = NarrativeStateMachine("my_story", total_chapters=80)
        nsm.set_progress(30)       # 已写 30 章
        nsm.plant_hook("h1", "神秘古剑的来历", chapter=5)
        nsm.resolve_hook("h1", chapter=30, note="古剑原来是封印钥匙")
        report = nsm.audit()       # 返回当前状态报告
    """

    def __init__(
        self,
        story_id: str,
        total_chapters: int = 80,
        title: str = "",
        data_dir: Optional[str] = None,
    ):
        self.story_id = story_id
        self.title = title or story_id
        self.total_chapters = total_chapters
        self.current_chapter: int = 0
        self.phase: NarrativePhase = NarrativePhase.OPENING
        self.hooks: dict[str, PlotHook] = {}
        self.chapters: list[ChapterRecord] = []
        self.tension_history: list[float] = []
        self.metadata: dict = {}
        self.data_dir = data_dir

    # ── 进度 ──────────────────────────────────────────

    @property
    def progress(self) -> float:
        """当前写完了多少（0.0 ~ 1.0）"""
        if self.total_chapters <= 0:
            return 0.0
        return min(self.current_chapter / self.total_chapters, 1.0)

    def set_current_chapter(self, chapter: int) -> None:
        """推进到指定章节并自动调整阶段"""
        self.current_chapter = min(chapter, self.total_chapters)
        self.phase = NarrativePhase.from_progress(self.progress)

    def advance(self, chapters: int = 1) -> None:
        """前进 n 章"""
        self.set_current_chapter(self.current_chapter + chapters)

    # ── 伏笔管理 ──────────────────────────────────────

    def plant_hook(
        self, hook_id: str, description: str, chapter: int, category: str = "general"
    ) -> Optional[PlotHook]:
        """埋下伏笔（收敛期后禁止开新伏笔）"""
        if not self.phase.allows_new_hooks():
            return None  # 收敛期已过，不准再埋新伏笔
        hook = PlotHook(
            id=hook_id,
            description=description,
            chapter_planted=chapter,
            category=category,
        )
        self.hooks[hook_id] = hook
        return hook

    def resolve_hook(self, hook_id: str, chapter: int, note: str = "") -> bool:
        """回收伏笔"""
        hook = self.hooks.get(hook_id)
        if hook is None or hook.is_resolved:
            return False
        hook.is_resolved = True
        hook.chapter_resolved = chapter
        hook.resolution_note = note
        return True

    def pending_hooks(self) -> list[PlotHook]:
        """未回收的伏笔"""
        return [h for h in self.hooks.values() if not h.is_resolved]

    def resolved_hooks(self) -> list[PlotHook]:
        return [h for h in self.hooks.values() if h.is_resolved]

    def hook_resolution_rate(self) -> float:
        """伏笔回收率"""
        total = len(self.hooks)
        if total == 0:
            return 1.0
        return sum(1 for h in self.hooks.values() if h.is_resolved) / total

    # ── 章节记录 ──────────────────────────────────────

    def record_chapter(
        self,
        number: int,
        title: str = "",
        word_count: int = 0,
        tension: float = 0.0,
        summary: str = "",
    ) -> ChapterRecord:
        """记录已写章节"""
        rec = ChapterRecord(
            number=number,
            title=title,
            word_count=word_count,
            tension_score=tension,
            summary=summary,
        )
        # 替换或追加
        for i, r in enumerate(self.chapters):
            if r.number == number:
                self.chapters[i] = rec
                break
        else:
            self.chapters.append(rec)
        self.tension_history.append(tension)
        return rec

    # ── 审计报告 ──────────────────────────────────────

    def audit(self) -> dict:
        """
        生成当前叙事健康度报告
        返回值：
          phase, progress, hook_stats, tension, warnings
        """
        pending = self.pending_hooks()
        resolved = self.resolved_hooks()
        rate = self.hook_resolution_rate()
        avg_tension = sum(self.tension_history[-5:]) / max(
            len(self.tension_history[-5:]), 1
        )

        warnings = []
        if self.phase.requires_hook_resolution() and rate < 0.8:
            warnings.append(f"收敛期要求伏笔回收率 ≥80%，当前 {rate:.0%}")
        if avg_tension < 30 and self.phase in (
            NarrativePhase.CONVERGENCE,
            NarrativePhase.FINALE,
        ):
            warnings.append(
                f"终章阶段张力偏低 ({avg_tension:.0f}/100)，建议提高冲突密度"
            )
        if len(pending) > 10 and self.phase == NarrativePhase.CONVERGENCE:
            warnings.append(f"收敛期仍有 {len(pending)} 条伏笔未回收")

        return {
            "story_id": self.story_id,
            "title": self.title,
            "phase": self.phase.value,
            "phase_label": self.phase.label_cn(),
            "progress": round(self.progress, 4),
            "current_chapter": self.current_chapter,
            "total_chapters": self.total_chapters,
            "hook_stats": {
                "total": len(self.hooks),
                "pending": len(pending),
                "resolved": len(resolved),
                "resolution_rate": round(rate, 4),
            },
            "tension": {
                "average": round(avg_tension, 1),
                "history": [round(t, 1) for t in self.tension_history[-20:]],
            },
            "warnings": warnings,
            "healthy": len(warnings) == 0,
        }

    def suggest_next_chapter_focus(self) -> str:
        """
        根据当前阶段建议下一章的写作重点
        """
        rate = self.hook_resolution_rate()
        pending = self.pending_hooks()

        if self.phase == NarrativePhase.OPENING:
            return "开局阶段：建立世界观基调，引入主角与核心冲突，埋下 2-3 条关键伏笔"
        if self.phase == NarrativePhase.DEVELOPMENT:
            return "展开阶段：深化角色关系，推进主线，定期回收旧伏笔并埋设新钩子"
        if self.phase == NarrativePhase.CONVERGENCE:
            unresolved = [h.description for h in pending[:5]]
            hints = "；".join(unresolved) if unresolved else "无未回收伏笔"
            return f"收敛阶段：停止新伏笔！优先回收已有线索。待回收：{hints}"
        if self.phase == NarrativePhase.FINALE:
            return f"终章阶段：全力冲向结局，所有线索必须回收（当前回收率 {rate:.0%}），保持高密度冲突"

        return "继续推进剧情"

    # ── 序列化 ────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "title": self.title,
            "total_chapters": self.total_chapters,
            "current_chapter": self.current_chapter,
            "phase": self.phase.value,
            "hooks": {k: v.to_dict() for k, v in self.hooks.items()},
            "chapters": [c.to_dict() for c in self.chapters],
            "tension_history": self.tension_history,
            "metadata": self.metadata,
        }

    def save(self, path: Optional[str] = None) -> None:
        """保存状态到 JSON 文件"""
        target = path or (
            self.data_dir and str(Path(self.data_dir) / f"{self.story_id}_state.json")
        )
        if not target:
            return
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str) -> "NarrativeStateMachine":
        """从 JSON 文件恢复状态"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        nsm = cls(data["story_id"], data["total_chapters"], data["title"])
        nsm.current_chapter = data["current_chapter"]
        nsm.phase = NarrativePhase(data["phase"])
        nsm.hooks = {k: PlotHook(**v) for k, v in data.get("hooks", {}).items()}
        nsm.chapters = [ChapterRecord(**c) for c in data.get("chapters", [])]
        nsm.tension_history = data.get("tension_history", [])
        nsm.metadata = data.get("metadata", {})
        return nsm
