"""Chapter domain entity for the novel-authoring system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class Chapter:
    """Represents a single chapter within a story.

    Holds the full prose content, structural metadata (part, chapter
    number, scene breakdown), narrative hooks, and revision status.
    """

    VALID_STATUSES = {"draft", "revised", "polished", "final"}

    def __init__(
        self,
        id: Optional[str] = None,
        story_id: str = "",
        title: str = "",
        content: str = "",
        summary: str = "",
        chapter_number: int = 0,
        part: str = "",
        word_count: int = 0,
        status: str = "draft",
        pov_character_id: str = "",
        scenes: Optional[List[Dict[str, Any]]] = None,
        hooks: Optional[List[str]] = None,
        notes: str = "",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        self.id = id or uuid4().hex[:12]
        self.story_id = story_id
        self.title = title
        self.content = content
        self.summary = summary
        self.chapter_number = chapter_number
        self.part = part
        self.word_count = word_count
        self.status = status
        self.pov_character_id = pov_character_id
        self.scenes = scenes or []
        self.hooks = hooks or []
        self.notes = notes
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

        self._validate()

    # ── invariants ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if self.status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}. "
                f"Must be one of {sorted(self.VALID_STATUSES)}."
            )
        if self.chapter_number < 0:
            raise ValueError("chapter_number must be non-negative.")

    # ── public behaviour ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Chapter to a plain dictionary."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "chapter_number": self.chapter_number,
            "part": self.part,
            "word_count": self.word_count,
            "status": self.status,
            "pov_character_id": self.pov_character_id,
            "scenes": self.scenes,
            "hooks": self.hooks,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def recompute_word_count(self) -> None:
        """Recalculate *word_count* from the current *content* length."""
        self.word_count = len(self.content.split())
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_scene(
        self,
        heading: str,
        summary: str,
        characters: Optional[List[str]] = None,
    ) -> None:
        """Append a scene breakdown entry."""
        self.scenes.append(
            {
                "heading": heading,
                "summary": summary,
                "characters": characters or [],
            }
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_hook(self, hook: str) -> None:
        """Append a narrative hook / cliffhanger (idempotent)."""
        hook = hook.strip()
        if hook and hook not in self.hooks:
            self.hooks.append(hook)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    # ── factory ─────────────────────────────────────────────────────────────

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Chapter":
        """Build a Chapter instance from a dictionary."""
        return Chapter(
            id=data.get("id"),
            story_id=data.get("story_id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            chapter_number=data.get("chapter_number", 0),
            part=data.get("part", ""),
            word_count=data.get("word_count", 0),
            status=data.get("status", "draft"),
            pov_character_id=data.get("pov_character_id", ""),
            scenes=data.get("scenes"),
            hooks=data.get("hooks"),
            notes=data.get("notes", ""),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
