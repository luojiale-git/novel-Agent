"""
故事创作领域模型
=================
融合自 novel-agent 的 DDD 资产，以天机风格重写。

包含:
  - WorldBuilding   : 世界观构建（五大维度：law, geography, society, history, daily）
  - KnowledgeTriple : 知识三元组（SPO 事实断言，用于一致性检查）
  - StoryEvents     : 领域事件（事件驱动的架构通知）
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════
# WorldBuilding — 世界观
# ═══════════════════════════════════════════════════════════

WORLD_CATEGORIES = {"law", "geography", "society", "history", "daily"}


class WorldBuilding:
    """世界观构建条目 —— 故事世界的一个维度。

    每个条目捕获某一特定类目下的规则、命名实体和关系，
    用于维持故事世界的内在一致性。
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
        self.id = id or uuid.uuid4().hex[:12]
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

    def _validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("World-building 条目必须有一个非空名称。")
        if self.category not in WORLD_CATEGORIES:
            raise ValueError(
                f"无效类别 {self.category!r}。必须是 {sorted(WORLD_CATEGORIES)} 之一。"
            )

    def to_dict(self) -> Dict[str, Any]:
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
        self.entities.append(
            {"name": name, "description": description, "attributes": attributes or {}}
        )
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "WorldBuilding":
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
        return sorted(WORLD_CATEGORIES)


# ═══════════════════════════════════════════════════════════
# KnowledgeTriple — 知识三元组
# ═══════════════════════════════════════════════════════════


class KnowledgeTriple:
    """故事知识图谱的最小原子单元 —— 主-谓-宾 事实断言。

    三元组是从故事内容中提取的事实、关系和断言，
    用于一致性检查与叙事分析。
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
        self.id = id or uuid.uuid4().hex[:12]
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

    def _validate(self) -> None:
        if not self.subject or not self.subject.strip():
            raise ValueError("三元组主语不能为空。")
        if not self.predicate or not self.predicate.strip():
            raise ValueError("三元组谓语不能为空。")
        if not self.object or not self.object.strip():
            raise ValueError("三元组宾语不能为空。")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("置信度必须在 0.0 到 1.0 之间。")

    def to_dict(self) -> Dict[str, Any]:
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

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "KnowledgeTriple":
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
        """从文本中启发式提取三元组。

        支持格式:
          - subject | predicate | object
          - subject -- predicate --> object
          - subject is object
          - subject has object
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
                            confidence=0.7,
                        )
                        triples.append(triple)
                    break
        return triples


# ═══════════════════════════════════════════════════════════
# StoryEvents — 故事创作领域事件
# ═══════════════════════════════════════════════════════════


@dataclass
class DomainEvent:
    """领域事件基类"""

    event_id: str = ""
    timestamp: str = ""
    aggregate_id: str = ""

    def __post_init__(self):
        if not self.event_id:
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
    revision_type: str = ""


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


# 事件总线 — 简化版（发布/订阅模式）
EventHandler = Any  # Callable[[DomainEvent], None], 避免循环导入


class EventBus:
    """轻量级领域事件总线"""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def register(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        event_type = type(event).__name__
        for handler in self._handlers.get(event_type, []):
            handler(event)

    def reset(self) -> None:
        self._handlers.clear()


# 全局事件总线单例
event_bus = EventBus()
