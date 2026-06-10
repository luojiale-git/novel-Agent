"""
叙事记忆 — Narrative Memory
=============================
基于 SQLite FTS5 的轻量叙事语义检索。

无需外部依赖（Python 内置 sqlite3）。
FTS5 提供全文搜索，足以覆盖大多数叙事记忆检索场景。

记忆类型：
  - plot    : 情节事件
  - detail  : 细节设定（如角色喜好、物品描述）
  - note    : 作者笔记 / 灵感
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MemoryEntry:
    """单条记忆"""

    id: int = 0
    memory_type: str = "plot"  # plot | detail | note
    content: str = ""  # 记忆内容
    keywords: str = ""  # 逗号分隔关键词
    source_chapter: int = 0  # 来源章节
    importance: int = 5  # 重要性 1-10
    embedding: Optional[str] = None  # 预留：语义向量（JSON）
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "content": self.content,
            "keywords": self.keywords,
            "source_chapter": self.source_chapter,
            "importance": self.importance,
            "created_at": self.created_at,
        }


class NarrativeMemory:
    """
    叙事记忆 — 轻量语义检索

    用法:
        mem = NarrativeMemory("my_story.db")
        mem.store("plot", "林夜在幽都地下发现古剑", keywords="古剑,幽都", chapter=5)
        results = mem.search("古剑 来历")
        for r in results:
            print(r["content"], f"(相关度: {r['rank']})")
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = (
            str(Path(db_path).resolve()) if db_path != ":memory:" else ":memory:"
        )
        self._conn: Optional[sqlite3.Connection] = None

    # ── 连接管理 ──────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._create_conn()
        return self._conn

    def _create_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        self._init_schema(conn)
        return conn

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        """初始化表结构（含 FTS5 虚拟表）"""
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS narrative_memory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT    NOT NULL DEFAULT 'plot',
                content     TEXT    NOT NULL,
                keywords    TEXT    DEFAULT '',
                source_chapter INTEGER DEFAULT 0,
                importance  INTEGER DEFAULT 5,
                embedding   TEXT,
                created_at  REAL    NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
            USING fts5(content, keywords, content=narrative_memory, content_rowid=id);

            -- 触发器：保持 FTS 同步
            CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON narrative_memory BEGIN
                INSERT INTO memory_fts(rowid, content, keywords)
                VALUES (new.id, new.content, new.keywords);
            END;

            CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON narrative_memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, content, keywords)
                VALUES ('delete', old.id, old.content, old.keywords);
            END;

            CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON narrative_memory BEGIN
                INSERT INTO memory_fts(memory_fts, rowid, content, keywords)
                VALUES ('delete', old.id, old.content, old.keywords);
                INSERT INTO memory_fts(rowid, content, keywords)
                VALUES (new.id, new.content, new.keywords);
            END;
        """)

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "NarrativeMemory":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # ── 增删改 ────────────────────────────────────────

    def store(
        self,
        memory_type: str,
        content: str,
        *,
        keywords: str = "",
        chapter: int = 0,
        importance: int = 5,
    ) -> int:
        """
        存储一条记忆

        返回: 记忆 ID
        """
        cur = self.conn.execute(
            "INSERT INTO narrative_memory (memory_type, content, keywords, source_chapter, importance, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (memory_type, content, keywords, chapter, importance, time.time()),
        )
        self.conn.commit()
        return cur.lastrowid

    def get(self, memory_id: int) -> Optional[dict]:
        cur = self.conn.execute(
            "SELECT * FROM narrative_memory WHERE id = ?", (memory_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def update(self, memory_id: int, **kwargs) -> bool:
        """更新记忆字段"""
        allowed = {"content", "keywords", "source_chapter", "importance", "memory_type"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [memory_id]
        self.conn.execute(
            f"UPDATE narrative_memory SET {set_clause} WHERE id = ?", values
        )
        self.conn.commit()
        return True

    def delete(self, memory_id: int) -> bool:
        self.conn.execute("DELETE FROM narrative_memory WHERE id = ?", (memory_id,))
        self.conn.commit()
        return True

    # ── 检索 ──────────────────────────────────────────

    def search(self, query: str, limit: int = 10, memory_type: str = "") -> list[dict]:
        """
        FTS5 全文检索（BM25 排序）

        参数:
            query: 搜索关键词（FTS5 语法，支持 AND/OR/NOT）
            limit: 返回条数
            memory_type: 过滤类型（plot/detail/note）

        返回:
            [{id, content, keywords, rank, ...}]
        """
        if not query.strip():
            return self.list_recent(limit=limit, memory_type=memory_type)

        sql = """
            SELECT m.*, rank
            FROM memory_fts
            JOIN narrative_memory m ON memory_fts.rowid = m.id
            WHERE memory_fts MATCH ?
        """
        params: list = [query]

        if memory_type:
            sql += " AND m.memory_type = ?"
            params.append(memory_type)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        try:
            cur = self.conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.OperationalError as e:
            # FTS 查询语法错误时降级为 LIKE 搜索
            return self._fallback_search(query, limit, memory_type)

    def _fallback_search(
        self, query: str, limit: int = 10, memory_type: str = ""
    ) -> list[dict]:
        """LIKE 降级搜索"""
        sql = "SELECT * FROM narrative_memory WHERE (content LIKE ? OR keywords LIKE ?)"
        params: list = [f"%{query}%", f"%{query}%"]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)

        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)

        cur = self.conn.execute(sql, params)
        results = [dict(row) for row in cur.fetchall()]
        # 添加 rank 字段（静态排序）
        for i, r in enumerate(results):
            r["rank"] = i + 1
        return results

    def list_recent(self, limit: int = 20, memory_type: str = "") -> list[dict]:
        """最近记忆"""
        sql = "SELECT * FROM narrative_memory"
        params: list = []
        if memory_type:
            sql += " WHERE memory_type = ?"
            params.append(memory_type)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cur = self.conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def search_by_chapter(self, chapter: int, memory_type: str = "") -> list[dict]:
        """检索特定章节的记忆"""
        sql = "SELECT * FROM narrative_memory WHERE source_chapter = ?"
        params: list = [chapter]
        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)
        sql += " ORDER BY importance DESC"
        cur = self.conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def recall_context(self, query: str, window: int = 5) -> str:
        """
        生成叙事上下文摘要（供 LLM 使用）

        参数:
            query:  当前场景相关的关键词
            window: 相关章节窗口（前后各取多少章）

        返回: 格式化的上下文文本
        """
        # 语义检索
        semantic_matches = self.search(query, limit=10)

        # 找最近的章节记录
        chapters = set()
        for m in semantic_matches:
            ch = m.get("source_chapter", 0)
            if ch > 0:
                for c in range(max(1, ch - window), ch + window + 1):
                    chapters.add(c)

        # 汇总
        lines = ["📚 叙事记忆上下文:\n"]
        if semantic_matches:
            lines.append("【语义相关记忆】")
            for m in semantic_matches[:5]:
                ch_info = f" [第{m['source_chapter']}章]" if m["source_chapter"] else ""
                lines.append(f"  - {m['content']}{ch_info}")

        # 按重要性排序的章节记忆
        if chapters:
            lines.append("\n【相关章节记忆】")
            for ch in sorted(chapters):
                ch_memories = self.search_by_chapter(ch)
                for m in ch_memories[:3]:
                    if m["id"] not in {x["id"] for x in semantic_matches[:5]}:
                        lines.append(f"  [第{ch}章] {m['content']}")

        return "\n".join(lines)

    def count(self, memory_type: str = "") -> int:
        sql = "SELECT COUNT(*) FROM narrative_memory"
        if memory_type:
            sql += " WHERE memory_type = ?"
            cur = self.conn.execute(sql, (memory_type,))
        else:
            cur = self.conn.execute(sql)
        return cur.fetchone()[0]

    def clear(self) -> None:
        self.conn.execute("DELETE FROM narrative_memory")
        self.conn.commit()
