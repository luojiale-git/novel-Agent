"""
JSON 文件仓储实现

实现 ``domain/repositories/interfaces.py`` 中定义的全部 6 个仓储接口，
数据通过 ``json_file_helper`` 以 JSON 文件形式持久化。

文件布局::

    data/
    ├── stories_index.json                 # 故事列表索引
    ├── story_{sid}.json                   # 故事本体
    ├── outline_{sid}.json                 # 故事大纲
    ├── triples_{sid}.json                 # 知识三元组（单文件数组）
    ├── characters/{sid}/{cid}.json        # 角色（每角色一文件）
    ├── chapters/{sid}/{chid}.json         # 章节（每章节一文件）
    └── worldbuilding/{sid}/{wid}.json     # 世界观（每条目一文件）

.. note::

    本模块不依赖第三方 JSON 数据库；所有写入采用 **write-to-temp-then-rename**
    原子策略，单文件操作本身是安全的。跨实体的事务一致性由调用方保证。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from infrastructure.config.settings import settings

from domain.models.chapter import Chapter
from domain.models.character import Character
from domain.models.knowledge_triple import KnowledgeTriple
from domain.models.outline import Outline
from domain.models.story import Story
from domain.models.worldbuilding import WorldBuilding
from domain.repositories.interfaces import (
    ChapterRepository,
    CharacterRepository,
    KnowledgeTripleRepository,
    OutlineRepository,
    StoryRepository,
    UnitOfWork,
    WorldBuildingRepository,
)

from .json_file_helper import (
    CHARACTERS_DIR,
    CHAPTERS_DIR,
    WORLDBUILDING_DIR,
    character_path,
    characters_dir,
    chapter_path,
    chapters_dir,
    delete_json,
    list_json_files,
    load_stories_index,
    outline_path,
    read_json,
    remove_story_index_entry,
    save_stories_index,
    story_path,
    triples_path,
    upsert_story_index_entry,
    worldbuilding_dir,
    worldbuilding_path,
    write_json,
)

# ============================================================================
# 内部辅助
# ============================================================================


def _generic_get_by_id(
    base_dir: Path,
    entity_id: str,
) -> Optional[Any]:
    """在所有故事子目录中搜索指定 ID 的实体数据。

    遍历 *base_dir* 下的所有 ``{story_id}`` 子目录，
    找到 ID 匹配的 ``.json`` 文件。适用于 ``get(character_id)`` /
    ``get(chapter_id)`` 等只需要 ID 但不知道所属 story 的场景。
    """
    if not base_dir.exists():
        return None
    for story_subdir in base_dir.iterdir():
        if not story_subdir.is_dir():
            continue
        target = story_subdir / f"{entity_id}.json"
        if target.exists():
            data = read_json(target)
            if data and data.get("id") == entity_id:
                return data
    return None


def _generic_delete_by_id(
    base_dir: Path,
    entity_id: str,
) -> bool:
    """在所有故事子目录中搜索并删除指定 ID 的实体文件。"""
    if not base_dir.exists():
        return False
    for story_subdir in base_dir.iterdir():
        if not story_subdir.is_dir():
            continue
        target = story_subdir / f"{entity_id}.json"
        if target.exists():
            data = read_json(target)
            if data and data.get("id") == entity_id:
                return delete_json(target)
    return False


# ============================================================================
# JsonStoryRepository
# ============================================================================


class JsonStoryRepository(StoryRepository):
    """故事仓储 —— 每个故事一个 JSON 文件。"""

    def save(self, story: Story) -> Story:
        path = story_path(story.id)
        write_json(path, story.to_dict())
        # 同步索引
        upsert_story_index_entry(story.id, story.to_dict())
        return story

    def get(self, story_id: str) -> Optional[Story]:
        data = read_json(story_path(story_id))
        return Story.from_dict(data) if data else None

    def delete(self, story_id: str) -> bool:
        path = story_path(story_id)
        deleted = delete_json(path)
        if deleted:
            remove_story_index_entry(story_id)
        return deleted

    def list_all(self) -> list[dict]:
        return load_stories_index()

    def exists(self, story_id: str) -> bool:
        return story_path(story_id).exists()


# ============================================================================
# JsonCharacterRepository
# ============================================================================


class JsonCharacterRepository(CharacterRepository):
    """角色仓储 —— 按 ``characters/{story_id}/{char_id}.json`` 组织。"""

    def save(self, character: Character) -> Character:
        path = character_path(character.story_id, character.id)
        write_json(path, character.to_dict())
        return character

    def get(self, character_id: str) -> Optional[Character]:
        data = _generic_get_by_id(settings.data_dir_path / CHARACTERS_DIR, character_id)
        return Character.from_dict(data) if data else None

    def list_by_story(self, story_id: str) -> list[Character]:
        return _load_entities_from_dir(characters_dir(story_id), Character.from_dict)

    def delete(self, character_id: str) -> bool:
        return _generic_delete_by_id(
            settings.data_dir_path / CHARACTERS_DIR, character_id
        )


# ============================================================================
# JsonChapterRepository
# ============================================================================


class JsonChapterRepository(ChapterRepository):
    """章节仓储 —— 按 ``chapters/{story_id}/{chapter_id}.json`` 组织。"""

    def save(self, chapter: Chapter) -> Chapter:
        path = chapter_path(chapter.story_id, chapter.id)
        write_json(path, chapter.to_dict())
        return chapter

    def get(self, chapter_id: str) -> Optional[Chapter]:
        data = _generic_get_by_id(settings.data_dir_path / CHAPTERS_DIR, chapter_id)
        return Chapter.from_dict(data) if data else None

    def list_by_story(self, story_id: str) -> list[Chapter]:
        return _load_entities_from_dir(chapters_dir(story_id), Chapter.from_dict)

    def delete(self, chapter_id: str) -> bool:
        return _generic_delete_by_id(settings.data_dir_path / CHAPTERS_DIR, chapter_id)

    def max_chapter_number(self, story_id: str) -> int:
        chapters = self.list_by_story(story_id)
        if not chapters:
            return 0
        return max(ch.chapter_number for ch in chapters)


# ============================================================================
# JsonWorldBuildingRepository
# ============================================================================


class JsonWorldBuildingRepository(WorldBuildingRepository):
    """世界观仓储 —— 按 ``worldbuilding/{story_id}/{wb_id}.json`` 组织。"""

    def save(self, wb: WorldBuilding) -> WorldBuilding:
        path = worldbuilding_path(wb.story_id, wb.id)
        write_json(path, wb.to_dict())
        return wb

    def get(self, wb_id: str) -> Optional[WorldBuilding]:
        data = _generic_get_by_id(settings.data_dir_path / WORLDBUILDING_DIR, wb_id)
        return WorldBuilding.from_dict(data) if data else None

    def list_by_story(self, story_id: str) -> list[WorldBuilding]:
        return _load_entities_from_dir(
            worldbuilding_dir(story_id), WorldBuilding.from_dict
        )

    def delete(self, wb_id: str) -> bool:
        return _generic_delete_by_id(settings.data_dir_path / WORLDBUILDING_DIR, wb_id)


# ============================================================================
# JsonKnowledgeTripleRepository
# ============================================================================


class JsonKnowledgeTripleRepository(KnowledgeTripleRepository):
    """知识三元组仓储 —— 每部故事一个 ``triples_{story_id}.json`` 数组文件。"""

    def save(self, triple: KnowledgeTriple) -> KnowledgeTriple:
        path = triples_path(triple.story_id)
        existing = self.list_by_story(triple.story_id)

        # 替换已有（按 id 匹配），否则追加
        new_list: list[KnowledgeTriple] = []
        replaced = False
        for t in existing:
            if t.id == triple.id:
                new_list.append(triple)
                replaced = True
            else:
                new_list.append(t)
        if not replaced:
            new_list.append(triple)

        write_json(path, [t.to_dict() for t in new_list])
        return triple

    def list_by_story(self, story_id: str) -> list[KnowledgeTriple]:
        data = read_json(triples_path(story_id))
        if not isinstance(data, list):
            return []
        return [KnowledgeTriple.from_dict(item) for item in data]

    def search(self, story_id: str, query: str) -> list[KnowledgeTriple]:
        q = query.lower()
        all_triples = self.list_by_story(story_id)
        return [
            t
            for t in all_triples
            if q in t.subject.lower()
            or q in t.predicate.lower()
            or q in t.object.lower()
            or q in t.context.lower()
        ]

    def delete_by_story(self, story_id: str) -> None:
        delete_json(triples_path(story_id))


# ============================================================================
# JsonOutlineRepository
# ============================================================================


class JsonOutlineRepository(OutlineRepository):
    """大纲仓储 —— 每个故事大纲一个 ``outline_{story_id}.json`` 文件。"""

    def save(self, outline: Outline) -> Outline:
        write_json(outline_path(outline.story_id), outline.to_dict())
        return outline

    def get_by_story(self, story_id: str) -> Optional[Outline]:
        data = read_json(outline_path(story_id))
        return Outline.from_dict(data) if data else None

    def delete(self, outline_id: str) -> bool:
        """在所有 story 的 outline 文件中搜索匹配的 outline_id 并删除。"""
        import glob as glob_mod

        data_dir = outline_path("").parent
        pattern = str(data_dir / "outline_*.json")
        for path_str in glob_mod.glob(pattern):
            path = Path(path_str)
            data = read_json(path)
            if data and data.get("id") == outline_id:
                return delete_json(path)
        return False


# ============================================================================
# JsonUnitOfWork
# ============================================================================


class JsonUnitOfWork(UnitOfWork):
    """JSON 工作单元。

    JSON 文件本身是单文件原子写入，不存在跨文件的 ACID 事务。
    本 UoW 作为上下文管理器存在，满足接口契约，同时可被未来
    扩展为内存变更追踪 + 批量刷写的模式。
    """

    def __init__(self) -> None:
        self._committed = False
        self._rolled_back = False
        self._on_commit_hooks: list[Callable[[], None]] = []

    def __enter__(self) -> "JsonUnitOfWork":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if exc_type is not None:
            # 异常发生时自动回滚
            self.rollback()
        elif not self._committed and not self._rolled_back:
            self.commit()

    def commit(self) -> None:
        """提交变更。

        在当前实现中，仓储的每个 ``save`` 方法已经即时写入了文件，
        因此 commit 主要是运行注册的钩子。
        """
        if self._rolled_back:
            return
        self._committed = True
        for hook in self._on_commit_hooks:
            hook()

    def rollback(self) -> None:
        """回滚变更。

        当前实现不支持真正的回滚（JSON 无事务）。
        设置标记位防止重复 commit。
        """
        self._rolled_back = True

    def add_on_commit(self, hook: Callable[[], None]) -> None:
        """注册一个在 commit 时触发的回调。"""
        self._on_commit_hooks.append(hook)


# ============================================================================
# 内部辅助函数
# ============================================================================


def _load_entities_from_dir(
    directory: Path,
    from_dict: Callable[[Dict[str, Any]], Any],
) -> list:
    """从 *directory* 中读取所有 ``.json`` 文件并用 *from_dict* 反序列化。"""
    files = list_json_files(directory)
    result: list = []
    for f in files:
        data = read_json(f)
        if data:
            try:
                result.append(from_dict(data))
            except (KeyError, TypeError, ValueError):
                # 跳过格式不兼容的文件
                pass
    return result
