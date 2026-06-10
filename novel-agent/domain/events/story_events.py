"""
领域事件 - 故事相关的事件通知
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class DomainEvent:
    """领域事件基类"""

    event_id: str = ""
    timestamp: str = ""
    aggregate_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            import uuid

            self.event_id = uuid.uuid4().hex[:16]
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class StoryCreated(DomainEvent):
    title: str = ""
    genre: str = ""


@dataclass
class StoryUpdated(DomainEvent):
    changes: dict = field(default_factory=dict)


@dataclass
class ChapterWritten(DomainEvent):
    chapter_id: str = ""
    chapter_title: str = ""
    chapter_number: int = 0
    word_count: int = 0


@dataclass
class ChapterRevised(DomainEvent):
    chapter_id: str = ""
    revision_type: str = ""  # rewrite/expand/edit


@dataclass
class CharacterCreated(DomainEvent):
    character_id: str = ""
    name: str = ""
    role: str = ""


@dataclass
class CharacterUpdated(DomainEvent):
    character_id: str = ""
    changes: dict = field(default_factory=dict)


@dataclass
class OutlineGenerated(DomainEvent):
    outline_id: str = ""
    version: int = 1


@dataclass
class WorldBuilt(DomainEvent):
    world_id: str = ""
    category: str = ""


@dataclass
class KnowledgeTripleAdded(DomainEvent):
    triple_id: str = ""
    subject: str = ""
    predicate: str = ""
    object: str = ""


@dataclass
class StoryPhaseChanged(DomainEvent):
    old_phase: str = ""
    new_phase: str = ""
