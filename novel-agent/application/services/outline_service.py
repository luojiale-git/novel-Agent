"""
大纲应用服务
"""

import logging
from typing import Optional

from ...domain.models.outline import Outline
from ...domain.repositories.interfaces import OutlineRepository, StoryRepository
from ._base_service import _BaseService

logger = logging.getLogger(__name__)


class OutlineService(_BaseService):
    """大纲应用服务"""

    def __init__(self, repo: OutlineRepository, story_repo: StoryRepository):
        self.repo = repo
        self.story_repo = story_repo

    def get_by_story(self, story_id: str) -> Optional[dict]:
        outline = self.repo.get_by_story(story_id)
        return outline.to_dict() if outline else None

    def save(
        self,
        story_id: str,
        synopsis: str = "",
        logline: str = "",
        theme: str = "",
        tone: str = "",
        pacing: str = "medium",
        three_acts: Optional[dict] = None,
    ) -> Optional[dict]:
        """保存或更新大纲"""
        story = self.story_repo.get(story_id)
        if not story:
            return None

        existing = self.repo.get_by_story(story_id)
        now = self._now()

        if existing:
            existing.synopsis = synopsis or existing.synopsis
            existing.logline = logline or existing.logline
            existing.theme = theme or existing.theme
            existing.tone = tone or existing.tone
            existing.pacing = pacing or existing.pacing
            if three_acts:
                existing.three_acts = three_acts
            existing.advance_version()
            existing.updated_at = now
            saved = self.repo.save(existing)
        else:
            outline = Outline(
                id=self._generate_id("OL"),
                story_id=story_id,
                logline=logline,
                synopsis=synopsis,
                theme=theme,
                tone=tone,
                pacing=pacing,
                three_acts=three_acts or {},
                created_at=now,
                updated_at=now,
            )
            saved = self.repo.save(outline)

        # Update story
        story.outline = synopsis[:500] if synopsis else story.outline
        story.story_phase = "outline"
        self.story_repo.save(story)

        return saved.to_dict()

    def add_plot_thread(
        self,
        story_id: str,
        name: str,
        description: str,
        characters: Optional[list] = None,
    ) -> Optional[dict]:
        outline = self.repo.get_by_story(story_id)
        if not outline:
            return None
        outline.add_plot_thread(name, description, characters)
        outline.updated_at = self._now()
        saved = self.repo.save(outline)
        return saved.to_dict()

    def remove_plot_thread(self, story_id: str, thread_name: str) -> Optional[dict]:
        outline = self.repo.get_by_story(story_id)
        if not outline:
            return None
        outline.plot_threads = [
            t for t in outline.plot_threads if t.get("name") != thread_name
        ]
        outline.updated_at = self._now()
        saved = self.repo.save(outline)
        return saved.to_dict()

    def add_chapter_outline(
        self,
        story_id: str,
        title: str,
        summary: str = "",
        chapter_number: Optional[int] = None,
        beats: Optional[list] = None,
    ) -> Optional[dict]:
        """添加章节大纲（添加为 major event）"""
        outline = self.repo.get_by_story(story_id)
        if not outline:
            return None
        outline.add_event(
            chapter_number or 1, f"{title}: {summary}" if summary else title, beats
        )
        outline.updated_at = self._now()
        saved = self.repo.save(outline)
        return saved.to_dict()

    def delete(self, story_id: str) -> bool:
        return self.repo.delete(story_id)
