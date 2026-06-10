"""Knowledge-graph triple domain entity for the novel-authoring system."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class KnowledgeTriple:
    """A subject-predicate-object triple extracted from story content.

    Triples form the atomic unit of the story knowledge graph, capturing
    facts, relationships, and assertions that can be used for consistency
    checking and narrative analysis.
    """

    def __init__(
        self,
        id: Optional[str] = None,
        story_id: str = "",
        subject: str = "",
        predicate: str = "",
        object: str = "",
        confidence: float = 1.0,
        source: str = "",
        context: str = "",
        is_active: bool = True,
        created_at: Optional[str] = None,
    ) -> None:
        self.id = id or uuid4().hex[:12]
        self.story_id = story_id
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.confidence = confidence
        self.source = source
        self.context = context
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

        self._validate()

    # ── invariants ──────────────────────────────────────────────────────────

    def _validate(self) -> None:
        if not self.subject or not self.subject.strip():
            raise ValueError("Triple subject must be non-empty.")
        if not self.predicate or not self.predicate.strip():
            raise ValueError("Triple predicate must be non-empty.")
        if not self.object or not self.object.strip():
            raise ValueError("Triple object must be non-empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0 (inclusive).")

    # ── public behaviour ────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the triple to a plain dictionary."""
        return {
            "id": self.id,
            "story_id": self.story_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "source": self.source,
            "context": self.context,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }

    # ── factories ───────────────────────────────────────────────────────────

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "KnowledgeTriple":
        """Build a KnowledgeTriple from a dictionary."""
        return KnowledgeTriple(
            id=data.get("id"),
            story_id=data.get("story_id", ""),
            subject=data["subject"],
            predicate=data["predicate"],
            object=data["object"],
            confidence=data.get("confidence", 1.0),
            source=data.get("source", ""),
            context=data.get("context", ""),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
        )

    @staticmethod
    def from_text(text: str, story_id: str) -> List["KnowledgeTriple"]:
        """Parse triples from generated text using simple pattern matching.

        Attempts to extract ``<subject> <predicate> <object>`` patterns
        from each line of *text*.  Supported line formats:

        - ``subject | predicate | object``
        - ``subject -- predicate --> object``
        - ``subject is object``
        - ``subject has object``

        This is a heuristic parser intended for initial extraction;
        results should be reviewed for quality and accuracy.
        """
        patterns = [
            re.compile(r"(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)"),
            re.compile(r"(.+?)\s*--\s*(.+?)\s*-->\s*(.+)"),
            re.compile(r"(.+?)\s+is\s+(.+)"),
            re.compile(r"(.+?)\s+has\s+(.+)"),
        ]

        triples: List[KnowledgeTriple] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            for pattern in patterns:
                match = pattern.match(line)
                if match:
                    groups = match.groups()
                    subject = groups[0].strip()
                    predicate = groups[1].strip()
                    obj = groups[2].strip() if len(groups) > 2 else ""
                    if subject and predicate and obj:
                        triple = KnowledgeTriple(
                            story_id=story_id,
                            subject=subject,
                            predicate=predicate,
                            object=obj,
                            source="text_extraction",
                            context=line,
                            confidence=0.7,  # moderate confidence for auto-extraction
                        )
                        triples.append(triple)
                    break  # first matching pattern wins per line

        return triples
