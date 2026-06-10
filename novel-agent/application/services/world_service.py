"""
世界观应用服务
"""

import logging
from typing import Optional

from ...domain.models.worldbuilding import WorldBuilding
from ...domain.repositories.interfaces import WorldBuildingRepository, StoryRepository
from ._base_service import _BaseService

logger = logging.getLogger(__name__)


class WorldService(_BaseService):
    """世界观应用服务"""

    def __init__(self, repo: WorldBuildingRepository, story_repo: StoryRepository):
        self.repo = repo
        self.story_repo = story_repo

    def create(
        self,
        story_id: str,
        name: str,
        category: str = "geography",
        description: str = "",
    ) -> Optional[dict]:
        """创建世界观条目"""
        story = self.story_repo.get(story_id)
        if not story:
            return None

        now = self._now()
        wb = WorldBuilding(
            id=self._generate_id("WB"),
            story_id=story_id,
            name=name,
            category=category,
            description=description,
            created_at=now,
            updated_at=now,
        )
        saved = self.repo.save(wb)

        story.settings.append(
            {"id": saved.id, "name": saved.name, "category": saved.category}
        )
        self.story_repo.save(story)

        return saved.to_dict()

    def get(self, wb_id: str) -> Optional[dict]:
        return self._get(wb_id)

    def list_by_story(self, story_id: str) -> list[dict]:
        return self._list_as_dicts(self.repo.list_by_story(story_id))

    def list_by_category(self, story_id: str, category: str) -> list[dict]:
        entries = self.repo.list_by_story(story_id)
        return [e.to_dict() for e in entries if e.category == category]

    def update(self, wb_id: str, **kwargs) -> Optional[dict]:
        allowed = {"name", "category", "description", "rules", "consistency_notes"}
        return self._update(wb_id, allowed, **kwargs)

    def delete(self, wb_id: str) -> bool:
        return self.repo.delete(wb_id)

    def categories(self) -> list[str]:
        return WorldBuilding.categories()
