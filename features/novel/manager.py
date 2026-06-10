"""
小说故事数据管理器 — 增强版
- 统一使用 Story dataclass 作为内部模型
- 旧 JSON 读取时自动迁移至新格式
- 所有旧函数签名保持向后兼容
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import (
    Chapter,
    Character,
    DimensionEntry,
    Story,
    World,
    _new_id,
    _now,
    story_from_dict,
    story_to_dict,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "novels"


def _get_story_path(story_id: str) -> Path:
    return DATA_DIR / f"{story_id}.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── 内部读写 ────────────────────────────────────────────────


def _load_story(story_id: str) -> Optional[Story]:
    path = _get_story_path(story_id)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return story_from_dict(raw)


def _save_story(story: Story):
    _ensure_data_dir()
    data = story_to_dict(story)
    path = _get_story_path(story.id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================================================================== #
#  故事 CRUD
# ================================================================== #


def list_stories() -> list[dict]:
    """获取所有故事摘要列表（兼容旧格式）"""
    _ensure_data_dir()
    stories = []
    for f in sorted(DATA_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            s = story_from_dict(data)
            stories.append(
                {
                    "id": s.id,
                    "title": s.title,
                    "genre": s.genre,
                    "author": s.author,
                    "status": s.status,
                    "tags": s.tags,
                    "updated_at": s.updated_at,
                    "chapter_count": len(s.chapters),
                    "char_count": sum(len(c.content) for c in s.chapters),
                }
            )
        except Exception:
            continue
    return stories


def create_story(
    title: str,
    genre: str = "",
    description: str = "",
    author: str = "",
    tone: str = "",
    pov: str = "",
    target_audience: str = "",
    tags: Optional[list[str]] = None,
) -> dict:
    """创建新故事（支持新旧字段）"""
    story = Story(
        title=title,
        genre=genre,
        description=description,
        author=author,
        tone=tone,
        pov=pov,
        target_audience=target_audience,
        tags=tags or [],
    )
    _save_story(story)
    return story_to_dict(story)


def get_story(story_id: str) -> Optional[dict]:
    """获取完整故事数据（返回增强格式 dict）"""
    story = _load_story(story_id)
    if story is None:
        return None
    return story_to_dict(story)


def update_story(story_id: str, **kwargs) -> Optional[dict]:
    """更新故事字段（支持所有新字段）"""
    story = _load_story(story_id)
    if story is None:
        return None
    allowed = {
        "title",
        "genre",
        "description",
        "outline",
        "author",
        "tone",
        "pov",
        "target_audience",
        "status",
        "tags",
    }
    for key, value in kwargs.items():
        if value is not None and key in allowed:
            setattr(story, key, value)
    story.updated_at = _now()
    _save_story(story)
    return story_to_dict(story)


def delete_story(story_id: str) -> bool:
    path = _get_story_path(story_id)
    if not path.exists():
        return False
    path.unlink()
    return True


# ================================================================== #
#  人物 CRUD
# ================================================================== #


def add_character(
    story_id: str,
    name: str,
    role: str = "",
    traits: str = "",
    background: str = "",
    appearance: str = "",
    arc: str = "",
) -> Optional[dict]:
    story = _load_story(story_id)
    if story is None:
        return None
    char = Character(
        name=name,
        role=role,
        traits=traits,
        background=background,
        appearance=appearance,
        arc=arc,
    )
    story.characters.append(char)
    story.updated_at = _now()
    _save_story(story)
    # 返回 dict（包含新旧字段）
    return {
        "id": char.id,
        "name": char.name,
        "role": char.role,
        "traits": char.traits,
        "background": char.background,
        "appearance": char.appearance,
        "arc": char.arc,
    }


def update_character(story_id: str, char_id: str, **kwargs) -> Optional[dict]:
    story = _load_story(story_id)
    if story is None:
        return None
    allowed = {"name", "role", "traits", "background", "appearance", "arc"}
    for char in story.characters:
        if char.id == char_id:
            for key, value in kwargs.items():
                if value is not None and key in allowed:
                    setattr(char, key, value)
            story.updated_at = _now()
            _save_story(story)
            return {
                "id": char.id,
                "name": char.name,
                "role": char.role,
                "traits": char.traits,
                "background": char.background,
                "appearance": char.appearance,
                "arc": char.arc,
            }
    return None


def delete_character(story_id: str, char_id: str) -> bool:
    story = _load_story(story_id)
    if story is None:
        return False
    story.characters = [c for c in story.characters if c.id != char_id]
    story.updated_at = _now()
    _save_story(story)
    return True


# ================================================================== #
#  章节 CRUD
# ================================================================== #


def add_chapter(
    story_id: str,
    title: str,
    content: str = "",
    notes: str = "",
    status: str = "draft",
) -> Optional[dict]:
    story = _load_story(story_id)
    if story is None:
        return None
    chapter = Chapter(
        title=title,
        content=content,
        notes=notes,
        status=status,
        order_index=len(story.chapters),
        word_count=len(content),
    )
    story.chapters.append(chapter)
    story.updated_at = _now()
    _save_story(story)
    return {
        "id": chapter.id,
        "title": chapter.title,
        "content": chapter.content,
        "word_count": chapter.word_count,
        "notes": chapter.notes,
        "status": chapter.status,
        "order_index": chapter.order_index,
        "created_at": chapter.created_at,
        "updated_at": chapter.updated_at,
    }


def update_chapter(story_id: str, chapter_id: str, **kwargs) -> Optional[dict]:
    story = _load_story(story_id)
    if story is None:
        return None
    allowed = {"title", "content", "notes", "status"}
    for ch in story.chapters:
        if ch.id == chapter_id:
            for key, value in kwargs.items():
                if value is not None and key in allowed:
                    setattr(ch, key, value)
            if "content" in kwargs and kwargs["content"] is not None:
                ch.word_count = len(kwargs["content"])
            ch.updated_at = _now()
            story.updated_at = _now()
            _save_story(story)
            return {
                "id": ch.id,
                "title": ch.title,
                "content": ch.content,
                "word_count": ch.word_count,
                "notes": ch.notes,
                "status": ch.status,
                "order_index": ch.order_index,
                "created_at": ch.created_at,
                "updated_at": ch.updated_at,
            }
    return None


def delete_chapter(story_id: str, chapter_id: str) -> bool:
    story = _load_story(story_id)
    if story is None:
        return False
    story.chapters = [ch for ch in story.chapters if ch.id != chapter_id]
    # 重新编号
    for idx, ch in enumerate(story.chapters):
        ch.order_index = idx
    story.updated_at = _now()
    _save_story(story)
    return True


def get_chapter(story_id: str, chapter_id: str) -> Optional[dict]:
    story = _load_story(story_id)
    if story is None:
        return None
    for ch in story.chapters:
        if ch.id == chapter_id:
            return {
                "id": ch.id,
                "title": ch.title,
                "content": ch.content,
                "word_count": ch.word_count,
                "notes": ch.notes,
                "status": ch.status,
                "order_index": ch.order_index,
                "created_at": ch.created_at,
                "updated_at": ch.updated_at,
            }
    return None


# ================================================================== #
#  世界观 CRUD
# ================================================================== #


def add_world_dimension(
    story_id: str, name: str, description: str = ""
) -> Optional[dict]:
    """为世界观添加一个维度/地点条目"""
    story = _load_story(story_id)
    if story is None:
        return None
    entry = DimensionEntry(name=name, description=description)
    story.world.dimensions.append(entry)
    story.updated_at = _now()
    _save_story(story)
    return {"name": entry.name, "description": entry.description}


def update_world(story_id: str, **kwargs) -> Optional[dict]:
    """更新世界观 — 支持 name/description/rules/background/dimensions"""
    story = _load_story(story_id)
    if story is None:
        return None
    simple_fields = {"name", "description", "rules", "background"}
    for key, value in kwargs.items():
        if value is not None and key in simple_fields:
            setattr(story.world, key, value)
    if "dimensions" in kwargs and kwargs["dimensions"] is not None:
        dims = []
        for d in kwargs["dimensions"]:
            if isinstance(d, DimensionEntry):
                dims.append(d)
            elif isinstance(d, dict):
                dims.append(DimensionEntry(**d))
        story.world.dimensions = dims
    story.updated_at = _now()
    _save_story(story)
    return {
        "name": story.world.name,
        "description": story.world.description,
        "rules": story.world.rules,
        "background": story.world.background,
        "dimensions": [d.__dict__ for d in story.world.dimensions],
    }


# ================================================================== #
#  新增便利方法
# ================================================================== #


def get_story_summary(story_id: str) -> Optional[dict]:
    """获取故事摘要（不含章节内容，适合列表展示）"""
    story = _load_story(story_id)
    if story is None:
        return None
    return {
        "id": story.id,
        "title": story.title,
        "author": story.author,
        "genre": story.genre,
        "description": story.description,
        "status": story.status,
        "tags": story.tags,
        "tone": story.tone,
        "pov": story.pov,
        "target_audience": story.target_audience,
        "char_count": sum(len(c.content) for c in story.chapters),
        "chapter_count": len(story.chapters),
        "character_count": len(story.characters),
        "updated_at": story.updated_at,
    }


def export_story_json(story_id: str) -> Optional[str]:
    """导出故事为完整 JSON 字符串"""
    story = _load_story(story_id)
    if story is None:
        return None
    return json.dumps(story_to_dict(story), ensure_ascii=False, indent=2)
