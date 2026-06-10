"""
故事管理器 - 基于 JSON 文件的故事/章节/人物存储
"""

import json
import os
from datetime import datetime
from typing import Optional, Union
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


class StoryManager:
    """管理多个小说故事的增删改查"""

    def __init__(self, data_dir: Union[str, Path, None] = None):
        self.data_dir = Path(data_dir or DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.stories_file = self.data_dir / "stories_index.json"
        self._init_storage()

    # ------------------------------------------------------------------ #
    # 内部存储初始化
    # ------------------------------------------------------------------ #
    def _init_storage(self):
        if not self.stories_file.exists():
            self.stories_file.write_text("[]", encoding="utf-8")

    def _read_index(self) -> list[dict]:
        return json.loads(self.stories_file.read_text(encoding="utf-8"))

    def _write_index(self, data: list[dict]):
        self.stories_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _story_path(self, story_id: str) -> Path:
        return self.data_dir / f"story_{story_id}.json"

    def _now(self) -> str:
        return datetime.now().isoformat()

    # ------------------------------------------------------------------ #
    # 故事 CRUD
    # ------------------------------------------------------------------ #
    def create_story(self, title: str, genre: str = "", description: str = "") -> dict:
        """创建新故事"""
        index = self._read_index()
        story_id = f"S{len(index) + 1:04d}"
        now = self._now()
        story = {
            "id": story_id,
            "title": title,
            "genre": genre,
            "description": description,
            "outline": "",
            "word_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        # 写入独立文件
        self._story_path(story_id).write_text(
            json.dumps(
                {**story, "characters": [], "chapters": [], "settings": []},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        # 更新索引
        idx_entry = {
            k: story[k] for k in ("id", "title", "genre", "created_at", "updated_at")
        }
        index.append(idx_entry)
        self._write_index(index)
        return story

    def list_stories(self) -> list[dict]:
        return self._read_index()

    def get_story(self, story_id: str) -> Optional[dict]:
        path = self._story_path(story_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def update_story(self, story_id: str, **kwargs) -> Optional[dict]:
        story = self.get_story(story_id)
        if story is None:
            return None
        allowed = {"title", "genre", "description", "outline"}
        for k, v in kwargs.items():
            if k in allowed:
                story[k] = v
        story["updated_at"] = self._now()
        story["word_count"] = sum(
            len(ch.get("content", "")) for ch in story.get("chapters", [])
        )
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # 更新索引
        self._sync_index(story_id, story)
        return story

    def delete_story(self, story_id: str) -> bool:
        path = self._story_path(story_id)
        if not path.exists():
            return False
        path.unlink()
        index = self._read_index()
        index = [s for s in index if s["id"] != story_id]
        self._write_index(index)
        return True

    def _sync_index(self, story_id: str, story: dict):
        index = self._read_index()
        for i, s in enumerate(index):
            if s["id"] == story_id:
                index[i] = {
                    k: story[k]
                    for k in ("id", "title", "genre", "created_at", "updated_at")
                }
                break
        self._write_index(index)

    # ------------------------------------------------------------------ #
    # 人物管理
    # ------------------------------------------------------------------ #
    def add_character(
        self,
        story_id: str,
        name: str,
        role: str = "",
        traits: str = "",
        background: str = "",
    ) -> Optional[dict]:
        story = self.get_story(story_id)
        if story is None:
            return None
        char = {
            "id": f"C{len(story['characters']) + 1:04d}",
            "name": name,
            "role": role,
            "traits": traits,
            "background": background,
        }
        story["characters"].append(char)
        story["updated_at"] = self._now()
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return char

    def update_character(self, story_id: str, char_id: str, **kwargs) -> Optional[dict]:
        story = self.get_story(story_id)
        if story is None:
            return None
        for char in story["characters"]:
            if char["id"] == char_id:
                allowed = {"name", "role", "traits", "background"}
                for k, v in kwargs.items():
                    if k in allowed:
                        char[k] = v
                story["updated_at"] = self._now()
                self._story_path(story_id).write_text(
                    json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                return char
        return None

    def delete_character(self, story_id: str, char_id: str) -> bool:
        story = self.get_story(story_id)
        if story is None:
            return False
        before = len(story["characters"])
        story["characters"] = [c for c in story["characters"] if c["id"] != char_id]
        if len(story["characters"]) == before:
            return False
        story["updated_at"] = self._now()
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    # ------------------------------------------------------------------ #
    # 章节管理
    # ------------------------------------------------------------------ #
    def add_chapter(
        self, story_id: str, title: str, content: str = ""
    ) -> Optional[dict]:
        story = self.get_story(story_id)
        if story is None:
            return None
        now = self._now()
        chapter = {
            "id": f"CH{len(story['chapters']) + 1:04d}",
            "title": title,
            "content": content,
            "chapter_number": len(story["chapters"]) + 1,
            "created_at": now,
            "updated_at": now,
        }
        story["chapters"].append(chapter)
        story["updated_at"] = now
        story["word_count"] = sum(
            len(ch.get("content", "")) for ch in story["chapters"]
        )
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return chapter

    def update_chapter(
        self, story_id: str, chapter_id: str, **kwargs
    ) -> Optional[dict]:
        story = self.get_story(story_id)
        if story is None:
            return None
        for ch in story["chapters"]:
            if ch["id"] == chapter_id:
                allowed = {"title", "content"}
                for k, v in kwargs.items():
                    if k in allowed:
                        ch[k] = v
                ch["updated_at"] = self._now()
                story["updated_at"] = self._now()
                story["word_count"] = sum(
                    len(c.get("content", "")) for c in story["chapters"]
                )
                self._story_path(story_id).write_text(
                    json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                return ch
        return None

    def delete_chapter(self, story_id: str, chapter_id: str) -> bool:
        story = self.get_story(story_id)
        if story is None:
            return False
        before = len(story["chapters"])
        story["chapters"] = [c for c in story["chapters"] if c["id"] != chapter_id]
        if len(story["chapters"]) == before:
            return False
        # 重排编号
        for i, ch in enumerate(story["chapters"]):
            ch["chapter_number"] = i + 1
        story["updated_at"] = self._now()
        story["word_count"] = sum(len(c.get("content", "")) for c in story["chapters"])
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True

    # ------------------------------------------------------------------ #
    # 设定管理
    # ------------------------------------------------------------------ #
    def add_setting(
        self, story_id: str, name: str, description: str = ""
    ) -> Optional[dict]:
        story = self.get_story(story_id)
        if story is None:
            return None
        setting = {
            "id": f"ST{len(story['settings']) + 1:04d}",
            "name": name,
            "description": description,
        }
        story["settings"].append(setting)
        story["updated_at"] = self._now()
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return setting

    def get_chapter(self, story_id: str, chapter_id: str) -> Optional[dict]:
        """获取单个章节"""
        story = self.get_story(story_id)
        if story is None:
            return None
        for ch in story.get("chapters", []):
            if ch["id"] == chapter_id:
                return ch
        return None

    def delete_setting(self, story_id: str, setting_id: str) -> bool:
        """删除设定"""
        story = self.get_story(story_id)
        if story is None:
            return False
        before = len(story["settings"])
        story["settings"] = [s for s in story["settings"] if s["id"] != setting_id]
        if len(story["settings"]) == before:
            return False
        story["updated_at"] = self._now()
        self._story_path(story_id).write_text(
            json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True
