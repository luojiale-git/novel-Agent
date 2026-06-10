"""应用配置管理 - 从环境变量读取全局配置。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class AppSettings:
    """全局应用配置。

    配置项通过环境变量注入，提供合理的默认值。
    """

    # ── 数据目录 ──────────────────────────────────────────────────────────
    data_dir: str = field(
        default_factory=lambda: os.getenv(
            "NOVEL_DATA_DIR",
            str(Path(__file__).resolve().parent.parent.parent / "backend" / "data"),
        )
    )

    # ── LLM / AI ──────────────────────────────────────────────────────────
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("NOVEL_API_KEY") or None
    )
    api_base: str = field(
        default_factory=lambda: os.getenv("NOVEL_API_BASE", "https://api.deepseek.com")
    )
    model: str = field(
        default_factory=lambda: os.getenv("NOVEL_MODEL", "deepseek-chat")
    )
    temperature: float = field(
        default_factory=lambda: float(os.getenv("NOVEL_TEMPERATURE", "0.8"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("NOVEL_MAX_TOKENS", "4096"))
    )

    # ── 文件命名 ──────────────────────────────────────────────────────────
    stories_index_file: str = "stories_index.json"
    story_file_template: str = "story_{story_id}.json"
    outline_file_template: str = "outline_{story_id}.json"
    triples_file_template: str = "triples_{story_id}.json"

    # ── 派生路径（运行时计算） ───────────────────────────────────────────
    _data_dir_path: Path = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._data_dir_path = Path(self.data_dir)
        self._data_dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def data_dir_path(self) -> Path:
        return self._data_dir_path

    @property
    def stories_index_path(self) -> Path:
        return self._data_dir_path / self.stories_index_file

    def story_path(self, story_id: str) -> Path:
        return self._data_dir_path / self.story_file_template.format(story_id=story_id)

    def outline_path(self, story_id: str) -> Path:
        return self._data_dir_path / self.outline_file_template.format(
            story_id=story_id
        )

    def triples_path(self, story_id: str) -> Path:
        return self._data_dir_path / self.triples_file_template.format(
            story_id=story_id
        )

    def is_demo_mode(self) -> bool:
        """当未配置 API key 时返回 True，表示走演示模式。"""
        return self.api_key is None or self.api_key.strip() == ""


# ── 全局单例 ──────────────────────────────────────────────────────────────
settings = AppSettings()
