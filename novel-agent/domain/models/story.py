"""Story aggregate root domain entity for the novel-authoring system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

# ---------------------------------------------------------------------------
# Predefined genres — custom genres outside this list are also permitted.
# ---------------------------------------------------------------------------
DEFAULT_GENRES: List[str] = [
    "fantasy",
    "science_fiction",
    "mystery",
    "romance",
    "thriller",
    "horror",
    "historical_fiction",
    "literary_fiction",
    "young_adult",
    "adventure",
    "dystopian",
    "paranormal",
    "realistic_fiction",
    "magical_realism",
    "graphic_novel",
    "poetry",
    "drama",
    "action",
    "comedy",
    "satire",
]


class Story:
    """Aggregate root for a story / novel.

    Encapsulates top-level metadata and owns lightweight references to
    characters, chapters, world-building settings, and tags.
    """

    VALID_STATUSES = {"draft", "outlining", "writing", "completed", "abandoned"}
    VALID_PHASES = {
        "concept",
        "outline",
        "drafting",
        "first_pass",
        "revising",
        "polished",
    }

    def __init__(
        self,
        id: str,
        title: str,
        genre: str,
        description: str,
        outline: str = "",
        word_count: int = 0,
        status: str = "draft",
        story_phase: str = "concept",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        characters: Optional[List[Dict[str, Any]]] = None,
        chapters: Optional[List[Dict[str, Any]]] = None,
        settings: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.id = id or uuid4().hex[:12]
        self.title = title
        self.genre = genre
        self.description = description
        self.outline = outline
        self.word_count = word_count
        self.status = status
        self.story_phase = story_phase
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at
        self.characters = characters or []
        self.chapters = chapters or []
        self.settings = settings or []
        self.tags = tags or []
        self.metadata = metadata or {}

        self._validate()

    # ── invariants ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        """Validate core invariants of the Story aggregate."""
        if not self.title or not self.title.strip():
            raise ValueError("Story title must be non-empty.")
        if not self.genre or not self.genre.strip():
            raise ValueError("Story genre must be non-empty.")
        if self.status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}. "
                f"Must be one of {sorted(self.VALID_STATUSES)}."
            )
        if self.story_phase not in self.VALID_PHASES:
            raise ValueError(
                f"Invalid story_phase {self.story_phase!r}. "
                f"Must be one of {sorted(self.VALID_PHASES)}."
            )

    # ── public behaviour ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Story to a plain dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "description": self.description,
            "outline": self.outline,
            "word_count": self.word_count,
            "status": self.status,
            "story_phase": self.story_phase,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "characters": self.characters,
            "chapters": self.chapters,
            "settings": self.settings,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    def update_word_count(self, chapters_content: List[str]) -> None:
        """Recompute *word_count* by summing word counts of chapter content strings."""
        total = 0
        for content in chapters_content:
            total += len(content.split())
        self.word_count = total
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_tag(self, tag: str) -> None:
        """Append a tag if not already present."""
        tag = tag.strip()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag if it exists (no-op otherwise)."""
        tag = tag.strip()
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    # ── factory ─────────────────────────────────────────────────────────────

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Story":
        """Build a Story instance from a dictionary (inverse of *to_dict*)."""
        return Story(
            id=data["id"],
            title=data["title"],
            genre=data["genre"],
            description=data["description"],
            outline=data.get("outline", ""),
            word_count=data.get("word_count", 0),
            status=data.get("status", "draft"),
            story_phase=data.get("story_phase", "concept"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            characters=data.get("characters"),
            chapters=data.get("chapters"),
            settings=data.get("settings"),
            tags=data.get("tags"),
            metadata=data.get("metadata"),
        )
