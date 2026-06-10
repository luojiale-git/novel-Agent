"""
故事应用服务 - CRUD + 业务编排
"""

import logging
from typing import Optional

from ...domain.models.story import Story
from ...domain.repositories.interfaces import StoryRepository
from ._base_service import _BaseService

logger = logging.getLogger(__name__)


class StoryService(_BaseService):
    """故事应用服务"""

    def __init__(self, repo: StoryRepository):
        self.repo = repo

    def create(self, title: str, genre: str = "", description: str = "") -> dict:
        """创建新故事"""
        story = Story(
            id=self._generate_id("S"),
            title=title,
            genre=genre,
            description=description,
            created_at=self._now(),
            updated_at=self._now(),
        )
        return self.repo.save(story).to_dict()

    def get(self, story_id: str) -> Optional[dict]:
        """获取故事"""
        return self._get(story_id)

    def update(self, story_id: str, **kwargs) -> Optional[dict]:
        """更新故事"""
        return self._update(
            story_id, {"title", "genre", "description", "outline"}, **kwargs
        )

    def delete(self, story_id: str) -> bool:
        """删除故事"""
        return self.repo.delete(story_id)

    def list_all(self) -> list[dict]:
        """列出所有故事"""
        return self._list_as_dicts(self.repo.list_all())

    def get_stats(self, story_id: str) -> dict:
        """获取故事统计"""
        story = self.repo.get(story_id)
        if not story:
            return {}
        return {
            "id": story.id,
            "title": story.title,
            "word_count": story.word_count,
            "status": story.status,
            "phase": story.story_phase,
            "chapter_count": len(story.chapters),
            "character_count": len(story.characters),
            "created_at": story.created_at,
            "updated_at": story.updated_at,
        }
