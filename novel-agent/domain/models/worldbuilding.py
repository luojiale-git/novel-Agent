"""World-building domain entity for the novel-authoring system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Five recognised world-building dimensions.
WORLD_CATEGORIES = {"law", "geography", "society", "history", "daily"}


class WorldBuilding:
    """Represents one dimension of world-building within a story.

    Each entry captures rules, named entities, and relations for a
    particular category (law, geography, society, history, or daily
    life) to help maintain internal consistency.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        story_id: str = "",
        name: str = "",
        category: str = "geography",
        description: str = "",
        rules: Optional[List[str]] = None,
        entities: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        consistency_notes: str = "",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        self.id = id or uuid4().hex[:12]
        self.story_id = story_id
        self.name = name
        self.category = category
        self.description = description
        self.rules = rules or []
        self.entities = entities or []
        self.relations = relations or []
        self.consistency_notes = consistency_notes
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

        self._validate()

    # ── invariants ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("World-building entry must have a non-empty name.")
        if self.category not in WORLD_CATEGORIES:
            raise ValueError(
                f"Invalid category {self.category!r}. "
                f"Must be one of {sorted(WORLD_CATEGORIES)}."
            )

    # ── public behaviour ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the WorldBuilding entry to a plain dictionary."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "rules": self.rules,
            "entities": self.entities,
            "relations": self.relations,
            "consistency_notes": self.consistency_notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def add_rule(self, rule: str) -> None:
        """Append a consistency rule (idempotent)."""
        rule = rule.strip()
        if rule and rule not in self.rules:
            self.rules.append(rule)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_entity(
        self,
        name: str,
        description: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a named entity within this world-building dimension."""
        self.entities.append(
            {
                "name": name,
                "description": description,
                "attributes": attributes or {},
            }
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()

    # ── factories ───────────────────────────────────────────────────────────

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "WorldBuilding":
        """Build a WorldBuilding instance from a dictionary."""
        return WorldBuilding(
            id=data.get("id"),
            story_id=data.get("story_id", ""),
            name=data["name"],
            category=data.get("category", "geography"),
            description=data.get("description", ""),
            rules=data.get("rules"),
            entities=data.get("entities"),
            relations=data.get("relations"),
            consistency_notes=data.get("consistency_notes", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @staticmethod
    def categories() -> List[str]:
        """Return the five recognised world-building dimensions."""
        return sorted(WORLD_CATEGORIES)
