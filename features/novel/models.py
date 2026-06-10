"""
统一领域模型 — 整合 novel-agent DDD 模型与天机数据层

作为数据契约，同时兼容旧格式的扁平 dict 存储。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


# ===================== Helpers ===================== #


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now().isoformat()


# ===================== 世界观五维模型 ===================== #


@dataclass
class DimensionEntry:
    """世界观的一个维度（如物理法则、社会结构、魔法系统等）"""

    category: str = ""  # 分类标签
    name: str = ""  # 维度名称
    description: str = ""  # 描述
    rules: list[str] = field(default_factory=list)  # 规则列表
    entities: list[str] = field(default_factory=list)  # 关键实体/概念
    relations: list[str] = field(default_factory=list)  # 相互关系


@dataclass
class World:
    """世界观设定"""

    name: str = ""
    description: str = ""
    rules: str = ""
    background: str = ""
    dimensions: list[DimensionEntry] = field(default_factory=list)


# ===================== 人物 ===================== #


@dataclass
class Character:
    """人物角色"""

    id: str = ""
    name: str = ""
    role: str = ""  # 主角/反派/配角/…
    traits: str = ""  # 性格特征
    background: str = ""  # 背景故事
    appearance: str = ""  # 外貌描写（新增）
    arc: str = ""  # 角色弧光（新增）

    def __post_init__(self):
        if not self.id:
            self.id = _new_id()


# ===================== 章节 ===================== #


@dataclass
class Chapter:
    """章节"""

    id: str = ""
    title: str = ""
    content: str = ""
    word_count: int = 0  # 字数统计（新增）
    notes: str = ""  # 作者备注（新增）
    status: str = "draft"  # draft / reviewing / done（新增）
    order_index: int = 0  # 排序（新增）
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = _now()
        if not self.id:
            self.id = _new_id()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.word_count:
            self.word_count = len(self.content)


# ===================== 故事 ===================== #


@dataclass
class Story:
    """故事聚合根"""

    id: str = ""
    title: str = "未命名"
    author: str = ""  # 作者（新增）
    genre: str = ""
    description: str = ""
    outline: str = ""
    tone: str = ""  # 风格基调（新增）
    pov: str = ""  # 视角（新增）
    target_audience: str = ""  # 目标读者（新增）
    status: str = "draft"  # draft / ongoing / completed（新增）
    tags: list[str] = field(default_factory=list)  # 标签（新增）
    state: dict = field(default_factory=dict)  # 故事运行状态数据
    world: World = field(default_factory=World)
    characters: list[Character] = field(default_factory=list)
    chapters: list[Chapter] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = _now()
        if not self.id:
            self.id = _new_id()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


# ===================== Dict 互转 ===================== #


def story_to_dict(story: Story) -> dict:
    """将 Story dataclass 转为可 JSON 序列化的 dict"""
    d = asdict(story)
    d["chapter_count"] = len(story.chapters)
    return d


def story_from_dict(data: dict) -> Story:
    """将 JSON dict 转为 Story dataclass（兼容旧格式）"""
    # 递归处理嵌套对象
    world_data = data.get("world", {})
    if isinstance(world_data, dict):
        if "dimensions" in world_data and isinstance(world_data["dimensions"], list):
            dims = [DimensionEntry(**d) for d in world_data["dimensions"]]
        else:
            dims = []
        world = World(
            name=world_data.get("name", ""),
            description=world_data.get("description", ""),
            rules=world_data.get("rules", ""),
            background=world_data.get("background", ""),
            dimensions=dims,
        )
    else:
        world = World()

    chars = []
    for c in data.get("characters", []):
        chars.append(
            Character(
                id=c.get("id", _new_id()),
                name=c.get("name", ""),
                role=c.get("role", ""),
                traits=c.get("traits", ""),
                background=c.get("background", ""),
                appearance=c.get("appearance", ""),
                arc=c.get("arc", ""),
            )
        )

    chapters = []
    for idx, ch in enumerate(data.get("chapters", [])):
        ch_content = ch.get("content", "")
        chapters.append(
            Chapter(
                id=ch.get("id", _new_id()),
                title=ch.get("title", f"第{idx + 1}章"),
                content=ch_content,
                word_count=ch.get("word_count", len(ch_content)),
                notes=ch.get("notes", ""),
                status=ch.get("status", "draft"),
                order_index=ch.get("order_index", idx),
                created_at=ch.get("created_at", _now()),
                updated_at=ch.get("updated_at", _now()),
            )
        )

    author_raw = data.get("author")
    # 旧格式没有 author 字段 → 标记为"未知作者"
    if not author_raw:
        author_raw = "未知作者"

    return Story(
        id=data.get("id", _new_id()),
        title=data.get("title", "未命名"),
        author=author_raw,
        genre=data.get("genre", ""),
        description=data.get("description", ""),
        outline=data.get("outline", ""),
        tone=data.get("tone", ""),
        pov=data.get("pov", ""),
        target_audience=data.get("target_audience", ""),
        status=data.get("status", "draft"),
        tags=data.get("tags", []),
        state=data.get("state", {}),
        world=world,
        characters=chars,
        chapters=chapters,
        created_at=data.get("created_at", _now()),
        updated_at=data.get("updated_at", _now()),
    )


# ===================== 快捷构造 ===================== #


def new_story(title: str, genre: str = "", description: str = "") -> Story:
    """从头创建一个新故事"""
    return Story(
        title=title,
        genre=genre,
        description=description,
    )
