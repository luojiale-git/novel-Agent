"""Outline (story blueprint) domain entity for the novel-authoring system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class Outline:
    """Blueprint / outline for a story.

    Holds the high-level narrative structure: logline, synopsis, theme,
    three-act breakdown, independent plot threads, and a timeline of
    major story events.  Versioned to support iterative outlining.
    """

    VALID_PACING = {"slow", "medium", "fast"}

    def __init__(
        self,
        id: Optional[str] = None,
        story_id: str = "",
        logline: str = "",
        synopsis: str = "",
        theme: str = "",
        target_audience: str = "",
        tone: str = "",
        pacing: str = "medium",
        estimated_chapters: int = 0,
        three_acts: Optional[Dict[str, Any]] = None,
        plot_threads: Optional[List[Dict[str, Any]]] = None,
        major_events: Optional[List[Dict[str, Any]]] = None,
        world_rules: Optional[List[str]] = None,
        version: int = 1,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        self.id = id or uuid4().hex[:12]
        self.story_id = story_id
        self.logline = logline
        self.synopsis = synopsis
        self.theme = theme
        self.target_audience = target_audience
        self.tone = tone
        self.pacing = pacing
        self.estimated_chapters = estimated_chapters
        self.three_acts = three_acts or {}
        self.plot_threads = plot_threads or []
        self.major_events = major_events or []
        self.world_rules = world_rules or []
        self.version = version
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

        self._validate()

    # ── invariants ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if self.pacing not in self.VALID_PACING:
            raise ValueError(
                f"Invalid pacing {self.pacing!r}. "
                f"Must be one of {sorted(self.VALID_PACING)}."
            )
        if self.estimated_chapters < 0:
            raise ValueError("estimated_chapters must be non-negative.")

    # ── public behaviour ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the Outline to a plain dictionary."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "logline": self.logline,
            "synopsis": self.synopsis,
            "theme": self.theme,
            "target_audience": self.target_audience,
            "tone": self.tone,
            "pacing": self.pacing,
            "estimated_chapters": self.estimated_chapters,
            "three_acts": self.three_acts,
            "plot_threads": self.plot_threads,
            "major_events": self.major_events,
            "world_rules": self.world_rules,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def advance_version(self) -> None:
        """Increment the outline version number and update timestamp."""
        self.version += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_plot_thread(
        self,
        name: str,
        description: str,
        characters: Optional[List[str]] = None,
    ) -> None:
        """Register a new plot thread."""
        self.plot_threads.append(
            {
                "name": name,
                "description": description,
                "characters": characters or [],
            }
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_event(
        self,
        chapter_num: int,
        event: str,
        characters: Optional[List[str]] = None,
    ) -> None:
        """Append a major story event (beat) to the timeline."""
        self.major_events.append(
            {
                "chapter_num": chapter_num,
                "event": event,
                "characters": characters or [],
            }
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()

    # ── factory ─────────────────────────────────────────────────────────────

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Outline":
        """Build an Outline instance from a dictionary."""
        return Outline(
            id=data.get("id"),
            story_id=data.get("story_id", ""),
            logline=data.get("logline", ""),
            synopsis=data.get("synopsis", ""),
            theme=data.get("theme", ""),
            target_audience=data.get("target_audience", ""),
            tone=data.get("tone", ""),
            pacing=data.get("pacing", "medium"),
            estimated_chapters=data.get("estimated_chapters", 0),
            three_acts=data.get("three_acts"),
            plot_threads=data.get("plot_threads"),
            major_events=data.get("major_events"),
            world_rules=data.get("world_rules"),
            version=data.get("version", 1),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
