"""
天机 - 代码搜索工具
支持基于内容和文件名的搜索
"""

import re
from pathlib import Path
from typing import Optional

from ..config import config
from ..utils.helpers import safe_path, setup_logger

logger = setup_logger("天机.CodeTools")


class CodeTools:
    """代码搜索与分析工具"""

    @staticmethod
    def grep(
        pattern: str, include: Optional[str] = None, path: Optional[str] = None
    ) -> str:
        """
        在文件中搜索内容（正则表达式）

        参数:
            pattern: 正则表达式
            include: 文件过滤模式，如 "*.py", "*.{ts,tsx}"
            path: 搜索目录

        返回:
            匹配结果列表
        """
        search_root = path if path else config.workspace_root or "."
        search_path = safe_path(search_root, config.workspace_root)

        results = []
        pattern_re = re.compile(pattern)

        # 使用 glob 过滤文件
        if include:
            import glob

            files = glob.glob(f"**/{include}", root_dir=search_path, recursive=True)
        else:
            # 无过滤时递归所有文件，但跳过常见二进制和隐藏目录
            files = []
            for p in search_path.rglob("*"):
                if p.is_file() and not any(
                    part.startswith(".") for part in p.relative_to(search_path).parts
                ):
                    files.append(str(p.relative_to(search_path)))

        for rel_path in files:
            full_path = search_path / rel_path
            try:
                # 跳过大文件
                if full_path.stat().st_size > 1024 * 1024:  # 1MB
                    continue

                # 尝试以文本方式读取
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        if pattern_re.search(line):
                            line = line.rstrip()
                            results.append(f"{rel_path}:{line_no}: {line[:200]}")
            except Exception:
                continue

        if not results:
            return f"未找到匹配 '{pattern}' 的内容"

        # 去重并限制结果数
        seen = set()
        unique = []
        for r in results:
            if r not in seen:
                seen.add(r)
                unique.append(r)

        total = len(unique)
        if total > 100:
            unique = unique[:100]

        output = f"搜索 '{pattern}' 找到 {total} 处匹配"
        if total > 100:
            output += " (仅显示前 100 条)"
        output += "\n" + "\n".join(unique)
        return output

    @staticmethod
    def find_files(pattern: str, search_path: Optional[str] = None) -> str:
        """
        按文件名模式查找文件

        参数:
            pattern: 文件名 glob 模式
            search_path: 搜索目录

        返回:
            文件列表
        """
        import glob

        base = search_path if search_path else config.workspace_root or "."
        base_path = safe_path(base, config.workspace_root)

        matches = sorted(glob.glob(f"**/{pattern}", root_dir=base_path, recursive=True))

        if not matches:
            return f"未找到 '{pattern}'"

        lines = [f"找到 {len(matches)} 个匹配 '{pattern}' 的文件:"]
        for m in matches:
            full = base_path / m
            size = full.stat().st_size if full.is_file() else 0
            label = f"{m} ({size / 1024:.1f} KB)" if full.is_file() else f"{m}/"
            lines.append(f"  {label}")

        return "\n".join(lines)

    @staticmethod
    def read_file_lines(file_path: str, offset: int = 1, limit: int = 50) -> str:
        """
        读取文件的指定行范围

        参数:
            file_path: 文件路径
            offset: 起始行号
            limit: 读取行数

        返回:
            带行号的内容
        """
        from .file_tools import FileTools

        return FileTools.read_file(file_path, offset=offset, limit=limit)
