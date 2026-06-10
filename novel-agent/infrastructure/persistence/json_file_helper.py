"""
JSON 文件 I/O 辅助工具

提供原子读写、路径管理、索引读写等底层操作。
所有文件操作集中在此，上层仓储实现只调用本模块的方法。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from infrastructure.config.settings import settings

T = TypeVar("T")

# ---------------------------------------------------------------------------
# 数据目录下的子目录常量
# ---------------------------------------------------------------------------
CHARACTERS_DIR = "characters"
CHAPTERS_DIR = "chapters"
WORLDBUILDING_DIR = "worldbuilding"


# ============================================================================
# 路径辅助
# ============================================================================


def _ensure_dir(path: Path) -> Path:
    """确保目录存在，返回传入的 *path*。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def story_path(story_id: str) -> Path:
    """返回 ``story_{story_id}.json`` 的完整路径。"""
    return settings.story_path(story_id)


def outline_path(story_id: str) -> Path:
    """返回 ``outline_{story_id}.json`` 的完整路径。"""
    return settings.outline_path(story_id)


def triples_path(story_id: str) -> Path:
    """返回 ``triples_{story_id}.json`` 的完整路径。"""
    return settings.triples_path(story_id)


def stories_index_path() -> Path:
    """返回 ``stories_index.json`` 的完整路径。"""
    return settings.stories_index_path


# ── 子目录路径 ──────────────────────────────────────────────────────────────


def characters_dir(story_id: str) -> Path:
    """返回 ``data/characters/{story_id}/``。"""
    return _ensure_dir(settings.data_dir_path / CHARACTERS_DIR / story_id)


def chapters_dir(story_id: str) -> Path:
    """返回 ``data/chapters/{story_id}/``。"""
    return _ensure_dir(settings.data_dir_path / CHAPTERS_DIR / story_id)


def worldbuilding_dir(story_id: str) -> Path:
    """返回 ``data/worldbuilding/{story_id}/``。"""
    return _ensure_dir(settings.data_dir_path / WORLDBUILDING_DIR / story_id)


def character_path(story_id: str, character_id: str) -> Path:
    """返回单个角色文件的完整路径。"""
    return characters_dir(story_id) / f"{character_id}.json"


def chapter_path(story_id: str, chapter_id: str) -> Path:
    """返回单个章节文件的完整路径。"""
    return chapters_dir(story_id) / f"{chapter_id}.json"


def worldbuilding_path(story_id: str, wb_id: str) -> Path:
    """返回单个世界观条目的完整路径。"""
    return worldbuilding_dir(story_id) / f"{wb_id}.json"


# ============================================================================
# 原子 JSON 读写
# ============================================================================


def read_json(file_path: Path) -> Optional[Any]:
    """从 *file_path* 读取 JSON 文件。

    返回 Python 对象（通常是 dict / list）；文件不存在时返回 ``None``。
    """
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise IOError(f"Failed to read JSON from {file_path}: {exc}") from exc


def write_json(file_path: Path, data: Any) -> None:
    """原子地将 *data* 写入 *file_path*。

    使用 **write-to-temp-then-rename** 策略，避免写操作中途崩溃导致文件损坏。
    """
    _ensure_dir(file_path.parent)
    tmp_path = file_path.parent / f".{file_path.name}.tmp.{os.getpid()}"
    try:
        tmp_content = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(tmp_content)
        tmp_path.replace(file_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def update_json(file_path: Path, updater: Callable[[Optional[Any]], Any]) -> Any:
    """原子读取-修改-写入：用 *updater* 处理当前内容再写回。

    ``updater`` 签名： ``updater(current: Any | None) -> new_data``。
    返回 *updater* 的返回值。
    """
    current = read_json(file_path)
    new_data = updater(current)
    write_json(file_path, new_data)
    return new_data


# ============================================================================
# 目录内文件枚举
# ============================================================================


def list_json_files(directory: Path) -> List[Path]:
    """返回 *directory* 下所有 ``.json`` 文件的排序列表（非递归）。"""
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def delete_json(file_path: Path) -> bool:
    """删除 *file_path*；已存在时返回 ``True``，否则返回 ``False``。"""
    if file_path.exists():
        file_path.unlink()
        return True
    return False


# ============================================================================
# 故事索引
# ============================================================================


INDEX_LOCK: Dict[str, Any] = {}  # 进程内锁（功能预留）


def load_stories_index() -> List[Dict[str, Any]]:
    """加载整个故事索引列表。文件不存在时返回空列表。"""
    path = stories_index_path()
    data = read_json(path)
    return data if isinstance(data, list) else []


def save_stories_index(index: List[Dict[str, Any]]) -> None:
    """全量覆写故事索引。"""
    write_json(stories_index_path(), index)


def update_stories_index(
    updater: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """原子更新故事索引。

    ``updater`` 签名： ``updater(current_index: list[dict]) -> new_index``。
    返回更新后的索引。
    """
    return update_json(stories_index_path(), updater)  # type: ignore[return-value]


def upsert_story_index_entry(story_id: str, entry: Dict[str, Any]) -> None:
    """在故事索引中插入或更新一条记录（按 *story_id* 匹配）。"""

    def _upsert(index: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        idx = index if isinstance(index, list) else []
        for i, item in enumerate(idx):
            if item.get("id") == story_id:
                idx[i] = entry
                return idx
        idx.append(entry)
        return idx

    update_stories_index(_upsert)


def remove_story_index_entry(story_id: str) -> None:
    """从索引中移除指定 *story_id* 的记录。"""

    def _remove(index: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        idx = index if isinstance(index, list) else []
        return [item for item in idx if item.get("id") != story_id]

    update_stories_index(_remove)
