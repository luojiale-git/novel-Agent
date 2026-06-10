"""
世界观管理器 — Story Bible
============================
轻量 JSON 存储，零外部依赖。

核心概念：
  - CharacterProfile : 角色档案（含动态状态快照 = 角色面具）
  - Location         : 地点设定
  - PlotHook         : 情节钩子（与 state_machine 联动）
  - StoryBible       : 世界观总管
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class CharacterTrait:
    """角色特质（用于角色面具的一致性检查）"""

    name: str
    category: str = "personality"  # personality | ability | habit | quirk | belief
    description: str = ""
    intensity: float = 1.0  # 0.0~1.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CharacterProfile:
    """
    角色档案 (含角色面具 CharacterMask)

    角色面具是角色在「当前叙事时刻」的动态状态快照。
    每次变更自动打版本标签。
    """

    id: str
    name: str
    role: str = ""  # 主角/反派/配角/...
    age: str = ""
    gender: str = ""
    appearance: str = ""  # 外貌描述
    personality: str = ""  # 性格概述
    background: str = ""  # 背景故事
    motivation: str = ""  # 核心动机
    arc: str = ""  # 角色弧光描述
    traits: list[CharacterTrait] = field(default_factory=list)
    relationships: dict[str, str] = field(default_factory=dict)  # 角色ID -> 关系描述
    current_state: dict = field(default_factory=dict)  # 角色面具：当前情绪/目标/状态
    notes: str = ""
    revision: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "age": self.age,
            "gender": self.gender,
            "appearance": self.appearance,
            "personality": self.personality,
            "background": self.background,
            "motivation": self.motivation,
            "arc": self.arc,
            "traits": [t.to_dict() for t in self.traits],
            "relationships": self.relationships,
            "current_state": self.current_state,
            "notes": self.notes,
            "revision": self.revision,
        }

    def update_state(self, **kwargs) -> None:
        """更新角色面具（当前动态状态）"""
        self.current_state.update(kwargs)
        self.revision += 1

    def get_mask_summary(self) -> str:
        """角色面具摘要：当前状态快照"""
        if not self.current_state:
            return f"{self.name}（状态无变化）"
        state_items = "；".join(f"{k}={v}" for k, v in self.current_state.items())
        return f"{self.name} [第{self.revision}版面具] {state_items}"

    def consistency_check(self, text_fragment: str) -> list[str]:
        """
        简易 OOC 检查：检查文本片段中是否出现与角色特质矛盾的说法
        实际使用时由 LLM 做深层判定，这里返回探测到的潜在冲突
        """
        issues = []
        text_lower = text_fragment.lower()
        name_lower = self.name.lower()
        if name_lower and name_lower not in text_lower:
            issues.append(f"文本未提及角色「{self.name}」，但上下文应涉及其出场")
        return issues


@dataclass
class Location:
    """地点设定"""

    id: str
    name: str
    type: str = "region"  # region | building | room | world
    description: str = ""
    atmosphere: str = ""
    connections: list[str] = field(default_factory=list)  # 关联地点ID
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class StoryBible:
    """
    世界观总管 — 聚合所有角色、地点、设定

    用法:
        bible = StoryBible("my_story")
        bible.add_character(CharacterProfile(id="c1", name="林夜", role="主角"))
        bible.add_location(Location(id="loc1", name="幽都", type="world"))
        bible.get_character("c1").update_state(mood="愤怒", goal="寻找真相")
    """

    def __init__(
        self, story_id: str = "default", title: str = "", data_dir: Optional[str] = None
    ):
        self.story_id = story_id
        self.title = title or story_id
        self.characters: dict[str, CharacterProfile] = {}
        self.locations: dict[str, Location] = {}
        self.settings: dict = {}  # 通用设定（魔法规则、科技水平等）
        self.global_notes: str = ""
        self.data_dir = data_dir

    # ── 角色管理 ──────────────────────────────────────

    def add_character(self, character: CharacterProfile) -> CharacterProfile:
        self.characters[character.id] = character
        return character

    def get_character(self, char_id: str) -> Optional[CharacterProfile]:
        return self.characters.get(char_id)

    def remove_character(self, char_id: str) -> bool:
        return self.characters.pop(char_id, None) is not None

    def list_characters(self, role: str = "") -> list[CharacterProfile]:
        if role:
            return [c for c in self.characters.values() if c.role == role]
        return list(self.characters.values())

    # ── 地点管理 ──────────────────────────────────────

    def add_location(self, location: Location) -> Location:
        self.locations[location.id] = location
        return location

    def get_location(self, loc_id: str) -> Optional[Location]:
        return self.locations.get(loc_id)

    def remove_location(self, loc_id: str) -> bool:
        return self.locations.pop(loc_id, None) is not None

    # ── 角色面具群检 ──────────────────────────────────

    def check_all_masks(self, text_fragment: str) -> list[str]:
        """对所有角色做 OOC 检查"""
        issues = []
        for char in self.characters.values():
            issues.extend(char.consistency_check(text_fragment))
        return issues

    # ── 序列化 ────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "title": self.title,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "settings": self.settings,
            "global_notes": self.global_notes,
        }

    def save(self, path: Optional[str] = None) -> None:
        target = path or (
            self.data_dir and str(Path(self.data_dir) / f"{self.story_id}_bible.json")
        )
        if not target:
            return
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str) -> "StoryBible":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        bible = cls(data["story_id"], data["title"])
        bible.characters = {
            k: CharacterProfile(
                id=v["id"],
                name=v["name"],
                role=v.get("role", ""),
                age=v.get("age", ""),
                gender=v.get("gender", ""),
                appearance=v.get("appearance", ""),
                personality=v.get("personality", ""),
                background=v.get("background", ""),
                motivation=v.get("motivation", ""),
                arc=v.get("arc", ""),
                traits=[CharacterTrait(**t) for t in v.get("traits", [])],
                relationships=v.get("relationships", {}),
                current_state=v.get("current_state", {}),
                notes=v.get("notes", ""),
                revision=v.get("revision", 0),
            )
            for k, v in data.get("characters", {}).items()
        }
        bible.locations = {
            k: Location(**v) for k, v in data.get("locations", {}).items()
        }
        bible.settings = data.get("settings", {})
        bible.global_notes = data.get("global_notes", "")
        return bible

    def summary(self) -> str:
        """返回圣经摘要文本"""
        lines = [
            f"📖 {self.title}",
            f"  角色: {len(self.characters)} 人",
            f"  地点: {len(self.locations)} 个",
        ]
        if self.characters:
            lines.append("  主要角色:")
            for c in self.characters.values():
                mask = c.get_mask_summary() if c.current_state else ""
                lines.append(f"    - {c.name} ({c.role}) {mask}")
        if self.global_notes:
            lines.append(f"  设定备注: {self.global_notes[:100]}")
        return "\n".join(lines)
