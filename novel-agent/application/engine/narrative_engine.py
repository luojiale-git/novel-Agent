"""
叙事引擎 - 故事生成管线的核心编排器
"""

import json
import logging
import re
from typing import Optional
from datetime import datetime, timezone

from ...domain.models.story import Story
from ...domain.models.chapter import Chapter
from ...domain.models.outline import Outline
from ...domain.repositories.interfaces import (
    StoryRepository,
    ChapterRepository,
    CharacterRepository,
    OutlineRepository,
    WorldBuildingRepository,
)
from ..ai.ai_gateway import AIGateway

logger = logging.getLogger(__name__)


class NarrativeEngine:
    """
    叙事引擎
    - 生成大纲、写章节、续写、改写、扩写
    - 自动推进故事阶段
    - 管理上下文构建
    """

    def __init__(
        self,
        ai: AIGateway,
        stories: StoryRepository,
        chapters: ChapterRepository,
        characters: CharacterRepository,
        outlines: OutlineRepository,
        world: WorldBuildingRepository,
    ):
        self.ai = ai
        self.stories = stories
        self.chapters = chapters
        self.characters = characters
        self.outlines = outlines
        self.world = world

    # ------------------------------------------------------------------ #
    # 公开 API
    # ------------------------------------------------------------------ #

    def generate_outline(self, story_id: str, instructions: str = "") -> dict:
        """生成故事大纲"""
        story = self.stories.get(story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")

        context = {
            "title": story.title,
            "genre": story.genre,
            "description": story.description,
            "instructions": instructions or "请生成一份详细的小说大纲",
        }

        result = self.ai.generate(
            "outline_generation", context, profile_name="creative"
        )
        outline_text = result["text"]

        # Parse and create Outline entity
        outline = Outline(
            id=f"OL-{story_id}",
            story_id=story_id,
            logline=self._extract_section(outline_text, "一句话梗概"),
            synopsis=self._extract_section(outline_text, "完整梗概") or outline_text,
            theme=self._extract_section(outline_text, "核心主题"),
            tone=self._extract_section(outline_text, "风格基调"),
            version=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.outlines.save(outline)

        # Update story
        story.outline = outline_text[:500]
        story.story_phase = "outline"
        story.status = "outlining"
        story.updated_at = datetime.now(timezone.utc).isoformat()
        self.stories.save(story)

        return {
            "outline_id": outline.id,
            "text": outline_text,
            "tokens": result["tokens"],
            "phase": "outline",
        }

    def write_chapter(
        self,
        story_id: str,
        chapter_title: str,
        chapter_summary: str = "",
    ) -> dict:
        """写一个新章节"""
        story = self.stories.get(story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")

        outline = self.outlines.get_by_story(story_id)
        chars = self.characters.list_by_story(story_id)
        all_chapters = self.chapters.list_by_story(story_id)
        world_entries = self.world.list_by_story(story_id)

        context = self._build_chapter_context(
            story,
            outline,
            chars,
            all_chapters,
            world_entries,
            chapter_title=chapter_title,
            chapter_summary=chapter_summary,
        )

        result = self.ai.generate("chapter_write", context, profile_name="writing")
        content = result["text"]

        chapter_num = len(all_chapters) + 1
        chapter = Chapter(
            id=f"CH{story_id}-{chapter_num:04d}",
            story_id=story_id,
            title=chapter_title,
            content=content,
            summary=chapter_summary,
            chapter_number=chapter_num,
            word_count=len(content),
            status="draft",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.chapters.save(chapter)

        # Update story
        story.word_count = sum(
            (c.word_count or len(c.content or ""))
            for c in self.chapters.list_by_story(story_id)
        )
        self._advance_phase(story)
        self.stories.save(story)

        return chapter.to_dict() | {"tokens": result["tokens"]}

    def continue_story(self, story_id: str) -> dict:
        """续写下一章"""
        story = self.stories.get(story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")

        all_chapters = self.chapters.list_by_story(story_id)
        if not all_chapters:
            raise ValueError("No chapters to continue from")

        last_chapter = all_chapters[-1]
        outline = self.outlines.get_by_story(story_id)
        chars = self.characters.list_by_story(story_id)
        world_entries = self.world.list_by_story(story_id)

        context = self._build_chapter_context(
            story,
            outline,
            chars,
            all_chapters,
            world_entries,
            chapter_title=f"第{len(all_chapters) + 1}章",
            chapter_summary=f"续写，上一章: {last_chapter.title}",
            last_chapter_content=last_chapter.content[:2000],
        )

        result = self.ai.generate("chapter_continue", context, profile_name="writing")
        content = result["text"]

        chapter_num = len(all_chapters) + 1
        chapter = Chapter(
            id=f"CH{story_id}-{chapter_num:04d}",
            story_id=story_id,
            title=f"第{chapter_num}章",
            content=content,
            chapter_number=chapter_num,
            word_count=len(content),
            status="draft",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.chapters.save(chapter)

        story.word_count += len(content)
        self._advance_phase(story)
        self.stories.save(story)

        return chapter.to_dict() | {"tokens": result["tokens"]}

    def rewrite_chapter(
        self, story_id: str, chapter_id: str, instructions: str
    ) -> dict:
        """改写指定章节"""
        chapter = self.chapters.get(chapter_id)
        if not chapter or chapter.story_id != story_id:
            raise ValueError(f"Chapter {chapter_id} not found in story {story_id}")

        context = {
            "content": chapter.content,
            "instructions": instructions,
            "title": chapter.title,
        }

        result = self.ai.generate("chapter_rewrite", context, profile_name="editing")
        new_content = result["text"]

        chapter.content = new_content
        chapter.word_count = len(new_content)
        chapter.status = "revised"
        chapter.updated_at = datetime.now(timezone.utc).isoformat()
        self.chapters.save(chapter)

        story = self.stories.get(story_id)
        if story:
            story.word_count = sum(
                (c.word_count or len(c.content or ""))
                for c in self.chapters.list_by_story(story_id)
            )
            self.stories.save(story)

        return chapter.to_dict() | {"tokens": result["tokens"]}

    def expand_chapter(self, story_id: str, chapter_id: str) -> dict:
        """扩写章节"""
        chapter = self.chapters.get(chapter_id)
        if not chapter or chapter.story_id != story_id:
            raise ValueError(f"Chapter {chapter_id} not found in story {story_id}")

        context = {
            "content": chapter.content,
            "title": chapter.title,
            "summary": chapter.summary,
        }

        result = self.ai.generate("chapter_expand", context, profile_name="writing")
        new_content = result["text"]

        chapter.content = new_content
        chapter.word_count = len(new_content)
        chapter.status = "revised"
        chapter.updated_at = datetime.now(timezone.utc).isoformat()
        self.chapters.save(chapter)

        story = self.stories.get(story_id)
        if story:
            story.word_count += len(new_content) - (chapter.word_count or 0)
            self.stories.save(story)

        return chapter.to_dict() | {"tokens": result["tokens"]}

    def analyze_story(self, story_id: str) -> dict:
        """分析故事一致性、节奏、漏洞等"""
        story = self.stories.get(story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")

        outline = self.outlines.get_by_story(story_id)
        chars = self.characters.list_by_story(story_id)
        all_chapters = self.chapters.list_by_story(story_id)

        context = {
            "title": story.title,
            "genre": story.genre,
            "description": story.description,
            "outline": outline.synopsis[:3000] if outline else "",
            "characters": json.dumps([c.to_dict() for c in chars], ensure_ascii=False)[
                :3000
            ],
            "chapters": json.dumps(
                [
                    {
                        "title": c.title,
                        "summary": c.summary,
                        "content_length": len(c.content or ""),
                    }
                    for c in all_chapters
                ],
                ensure_ascii=False,
            )[:5000],
            "story_phase": story.story_phase,
            "total_chapters": len(all_chapters),
            "total_words": story.word_count,
        }

        result = self.ai.generate("story_analysis", context, profile_name="analysis")
        return {
            "analysis": result["text"],
            "tokens": result["tokens"],
        }

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #

    def _build_chapter_context(
        self,
        story,
        outline,
        characters,
        chapters,
        world_entries,
        chapter_title="",
        chapter_summary="",
        last_chapter_content="",
    ) -> dict:
        """构建章节生成的上下文"""
        # Recent chapter summaries (last 3)
        recent_chapters = chapters[-3:] if chapters else []
        chapter_summaries = "\n".join(
            f"  CH{c.chapter_number}: {c.title} - {c.summary[:200]}"
            for c in recent_chapters
        )

        # Active characters
        active_chars = [c for c in characters if c.is_active][:5]
        char_descriptions = "\n".join(
            f"  {c.name} ({c.role}): {c.personality[:100]}, 目标: {c.motivation[:100]}"
            for c in active_chars
        )

        # World snippets
        world_snippets = "\n".join(
            f"  [{w.category}] {w.name}: {w.description[:200]}"
            for w in world_entries[:5]
        )

        return {
            "title": story.title,
            "genre": story.genre,
            "description": story.description[:500],
            "outline_synopsis": outline.synopsis[:2000]
            if outline and outline.synopsis
            else "",
            "three_acts": json.dumps(outline.three_acts, ensure_ascii=False)[:1000]
            if outline and outline.three_acts
            else "",
            "characters": char_descriptions,
            "chapter_summaries": chapter_summaries,
            "last_chapter": last_chapter_content[:2000] if last_chapter_content else "",
            "chapter_title": chapter_title,
            "chapter_summary": chapter_summary,
            "story_phase": story.story_phase,
            "world_settings": world_snippets,
        }

    def _advance_phase(self, story: Story):
        """根据章节数和字数自动推进故事阶段"""
        chapters_count = len(self.chapters.list_by_story(story.id))

        phase_map = [
            (0, "concept"),
            (1, "setup"),
            (4, "rising_action"),
            (10, "midpoint"),
            (18, "crisis"),
            (28, "climax"),
            (38, "falling_action"),
            (48, "resolution"),
        ]

        new_phase = "concept"
        for threshold, phase in reversed(phase_map):
            if chapters_count >= threshold:
                new_phase = phase
                break

        if new_phase != story.story_phase:
            old_phase = story.story_phase
            story.story_phase = new_phase
            logger.info(f"Story {story.id} phase advanced: {old_phase} -> {new_phase}")

    def _extract_section(self, text: str, section_name: str) -> str:
        """从生成的文本中提取指定章节（简单实现）"""
        pattern = rf"{section_name}[：:]\s*(.+?)(?:\n\n|\n[A-Z]|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()[:300]
        return ""
