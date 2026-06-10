"""
角色应用服务
"""

import logging
from typing import Optional

from ...domain.models.character import Character
from ...domain.repositories.interfaces import CharacterRepository, StoryRepository
from ._base_service import _BaseService

logger = logging.getLogger(__name__)


class CharacterService(_BaseService):
    """角色应用服务"""

    def __init__(self, repo: CharacterRepository, story_repo: StoryRepository):
        self.repo = repo
        self.story_repo = story_repo

    def create(
        self,
        story_id: str,
        name: str,
        role: str = "",
        traits: Optional[list[str]] = None,
        background: str = "",
        personality: str = "",
        motivation: str = "",
        appearance: str = "",
    ) -> Optional[dict]:
        """创建角色"""
        story = self.story_repo.get(story_id)
        if not story:
            return None

        now = self._now()
        char = Character(
            id=self._generate_id("C"),
            story_id=story_id,
            name=name,
            role=role or "supporting",
            traits=traits or [],
            background=background,
            personality=personality,
            motivation=motivation,
            appearance=appearance,
            created_at=now,
            updated_at=now,
        )
        saved = self.repo.save(char)

        # Update story reference
        story.characters.append(
            {"id": saved.id, "name": saved.name, "role": saved.role}
        )
        self.story_repo.save(story)

        return saved.to_dict()

    def get(self, character_id: str) -> Optional[dict]:
        return self._get(character_id)

    def list_by_story(self, story_id: str) -> list[dict]:
        return self._list_as_dicts(self.repo.list_by_story(story_id))

    def update(self, character_id: str, **kwargs) -> Optional[dict]:
        allowed = {
            "name",
            "role",
            "traits",
            "background",
            "personality",
            "motivation",
            "appearance",
            "arc",
            "is_active",
        }
        return self._update(character_id, allowed, **kwargs)

    def delete(self, character_id: str) -> bool:
        return self.repo.delete(character_id)

    def add_relationship(
        self, character_id: str, target_id: str, rel_type: str, description: str = ""
    ) -> Optional[dict]:
        char = self.repo.get(character_id)
        if not char:
            return None
        char.add_relationship(target_id, rel_type, description)
        saved = self.repo.save(char)
        return saved.to_dict()
