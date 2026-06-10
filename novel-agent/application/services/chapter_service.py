"""
章节应用服务
"""

import logging
from typing import Optional

from ...domain.models.chapter import Chapter
from ...domain.repositories.interfaces import ChapterRepository, StoryRepository
from ._base_service import _BaseService

logger = logging.getLogger(__name__)


class ChapterService(_BaseService):
    """章节应用服务"""

    def __init__(self, repo: ChapterRepository, story_repo: StoryRepository):
        self.repo = repo
        self.story_repo = story_repo

    def create(
        self,
        story_id: str,
        title: str,
        content: str = "",
        summary: str = "",
        chapter_number: Optional[int] = None,
    ) -> Optional[dict]:
        """创建章节"""
        story = self.story_repo.get(story_id)
        if not story:
            return None

        now = self._now()
        if chapter_number is None:
            chapter_number = self.repo.max_chapter_number(story_id) + 1

        chapter = Chapter(
            id=self._generate_id("CH"),
            story_id=story_id,
            title=title,
            content=content,
            summary=summary,
            chapter_number=chapter_number,
            word_count=len(content),
            status="draft",
            created_at=now,
            updated_at=now,
        )
        saved = self.repo.save(chapter)

        # Update story reference
        story.chapters.append(
            {"id": saved.id, "title": saved.title, "number": saved.chapter_number}
        )
        story.word_count = sum(
            (c.word_count or len(c.content or ""))
            for c in self.repo.list_by_story(story_id)
        )
        self.story_repo.save(story)

        return saved.to_dict()

    def get(self, chapter_id: str) -> Optional[dict]:
        return self._get(chapter_id)

    def list_by_story(self, story_id: str) -> list[dict]:
        return self._list_as_dicts(self.repo.list_by_story(story_id))

    def update(self, chapter_id: str, **kwargs) -> Optional[dict]:
        chapter = self.repo.get(chapter_id)
        if not chapter:
            return None
        allowed = {"title", "content", "summary", "status", "notes", "pov_character_id"}
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                setattr(chapter, k, v)
        chapter.word_count = len(chapter.content or "")
        chapter.updated_at = self._now()
        saved = self.repo.save(chapter)
        return saved.to_dict()

    def delete(self, chapter_id: str, story_id: str) -> bool:
        ok = self.repo.delete(chapter_id)
        if ok:
            story = self.story_repo.get(story_id)
            if story:
                story.chapters = [
                    c for c in story.chapters if c.get("id") != chapter_id
                ]
                story.word_count = sum(
                    (c.word_count or len(c.content or ""))
                    for c in self.repo.list_by_story(story_id)
                )
                self.story_repo.save(story)
        return ok
