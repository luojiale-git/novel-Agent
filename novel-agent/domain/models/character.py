"""Character domain entity for the novel-authoring system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class Character:
    """Represents a character within a story.

    Tracks biographical details, narrative role, relationships, voice
    attributes, and per-chapter appearance history.
    """

    VALID_ROLES = {
        "protagonist",
        "antagonist",
        "supporting",
        "mentor",
        "love_interest",
        "minor",
    }

    def __init__(
        self,
        id: Optional[str] = None,
        story_id: str = "",
        name: str = "",
        role: str = "supporting",
        traits: Optional[List[str]] = None,
        background: str = "",
        appearance: str = "",
        personality: str = "",
        motivation: str = "",
        arc: str = "",
        relationships: Optional[List[Dict[str, str]]] = None,
        voice_attributes: Optional[Dict[str, Any]] = None,
        chapters_appeared: Optional[List[str]] = None,
        is_active: bool = True,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        self.id = id or uuid4().hex[:12]
        self.story_id = story_id
        self.name = name
        self.role = role
        self.traits = traits or []
        self.background = background
        self.appearance = appearance
        self.personality = personality
        self.motivation = motivation
        self.arc = arc
        self.relationships = relationships or []
        self.voice_attributes = voice_attributes or {}
        self.chapters_appeared = chapters_appeared or []
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

        self._validate()

    # ── invariants ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Character name must be non-empty.")
        if self.role not in self.VALID_ROLES:
            raise ValueError(
                f"Invalid role {self.role!r}. "
                f"Must be one of {sorted(self.VALID_ROLES)}."
            )

    # ── public behaviour ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Character to a plain dictionary."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "name": self.name,
            "role": self.role,
            "traits": self.traits,
            "background": self.background,
            "appearance": self.appearance,
            "personality": self.personality,
            "motivation": self.motivation,
            "arc": self.arc,
            "relationships": self.relationships,
            "voice_attributes": self.voice_attributes,
            "chapters_appeared": self.chapters_appeared,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def add_relationship(
        self, target_id: str, rel_type: str, description: str = ""
    ) -> None:
        """Register a relationship with another character.

        If an identical *(target_id, rel_type)* pair already exists the
        description is updated; otherwise a new entry is appended.
        """
        now = datetime.now(timezone.utc).isoformat()
        for rel in self.relationships:
            if rel.get("target_id") == target_id and rel.get("type") == rel_type:
                rel["description"] = description
                self.updated_at = now
                return
        self.relationships.append(
            {"target_id": target_id, "type": rel_type, "description": description}
        )
        self.updated_at = now

    def remove_relationship(self, target_id: str) -> None:
        """Remove all relationships whose *target_id* matches."""
        before = len(self.relationships)
        self.relationships = [
            r for r in self.relationships if r.get("target_id") != target_id
        ]
        if len(self.relationships) < before:
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def record_appearance(self, chapter_id: str) -> None:
        """Mark the character as appearing in a given chapter (idempotent)."""
        if chapter_id not in self.chapters_appeared:
            self.chapters_appeared.append(chapter_id)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    # ── factory ─────────────────────────────────────────────────────────────

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Character":
        """Build a Character instance from a dictionary."""
        return Character(
            id=data.get("id"),
            story_id=data.get("story_id", ""),
            name=data["name"],
            role=data.get("role", "supporting"),
            traits=data.get("traits"),
            background=data.get("background", ""),
            appearance=data.get("appearance", ""),
            personality=data.get("personality", ""),
            motivation=data.get("motivation", ""),
            arc=data.get("arc", ""),
            relationships=data.get("relationships"),
            voice_attributes=data.get("voice_attributes"),
            chapters_appeared=data.get("chapters_appeared"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
