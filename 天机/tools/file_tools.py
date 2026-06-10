"""
天机 - 文件读写工具
安全的文件操作，含路径校验、大小限制、编码自动检测
"""

import os
import chardet
from pathlib import Path
from typing import Optional

from ..config import config
from ..utils.helpers import safe_path, setup_logger

logger = setup_logger("天机.FileTools")


class FileTools:
    """文件操作工具集"""

    @staticmethod
    def read_file(
        file_path: str, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> str:
        """
        读取文件内容

        参数:
            file_path: 文件路径
            offset: 起始行号（1-indexed，可选）
            limit: 最大行数（可选）

        返回:
            文件内容字符串（每行前带行号）
        """
        path = safe_path(file_path, config.workspace_root)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"路径是目录而非文件: {path}")

        # 检查文件大小
        file_size = path.stat().st_size
        if file_size > config.max_file_size:
            raise ValueError(
                f"文件过大 ({file_size / 1024 / 1024:.1f}MB)，"
                f"超过限制 ({config.max_file_size / 1024 / 1024:.1f}MB)"
            )

        # 自动检测编码
        with open(path, "rb") as f:
            raw = f.read()
        encoding = chardet.detect(raw)["encoding"] or "utf-8"

        # 读取内容
        content = raw.decode(encoding, errors="replace")
        lines = content.splitlines()
        total_lines = len(lines)

        # 计算偏移
        start = (offset - 1) if offset and offset > 0 else 0
        end = start + limit if limit else total_lines
        selected = lines[start:end]

        # 格式化输出
        result_lines = []
        for i, line in enumerate(selected, start=start + 1):
            result_lines.append(f"{i}: {line}")

        info = f"文件: {path} ({total_lines} 行, {file_size / 1024:.1f} KB)"
        if offset or limit:
            info += f" [显示行 {start + 1}-{end}]"

        return info + "\n" + "\n".join(result_lines)

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        """
        写入文件（不存在则创建）

        参数:
            file_path: 文件路径
            content: 文件内容

        返回:
            操作结果信息
        """
        path = safe_path(file_path, config.workspace_root)

        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        size = path.stat().st_size
        logger.info(f"已写入文件: {path} ({size} 字节)")
        return f"[完成] 已写入 {path} ({size} 字节)"

    @staticmethod
    def edit_file(
        file_path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> str:
        """
        编辑文件（精确字符串替换）

        参数:
            file_path: 文件路径
            old_string: 被替换的文本
            new_string: 替换后的文本
            replace_all: 是否替换所有匹配项

        返回:
            操作结果信息
        """
        path = safe_path(file_path, config.workspace_root)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_string not in content:
            raise ValueError(f"在文件中未找到匹配文本:\n---\n{old_string}\n---")

        if replace_all:
            count = content.count(old_string)
            new_content = content.replace(old_string, new_string)
        else:
            if content.count(old_string) > 1:
                raise ValueError(
                    f"找到 {content.count(old_string)} 处匹配。"
                    "请提供更多上下文，或使用 replace_all=True"
                )
            count = 1
            new_content = content.replace(old_string, new_string, 1)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"已编辑 {path}: 替换 {count} 处")
        return f"[完成] 已替换 {count} 处，文件: {path}"

    @staticmethod
    def list_directory(dir_path: str) -> str:
        """
        列出目录内容

        参数:
            dir_path: 目录路径

        返回:
            目录列表
        """
        path = safe_path(dir_path, config.workspace_root)

        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"路径不是目录: {path}")

        entries = []
        for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name)):
            suffix = "/" if entry.is_dir() else ""
            size = entry.stat().st_size if entry.is_file() else 0
            modified = entry.stat().st_mtime
            entries.append(f"{entry.name}{suffix}")

        return f"目录: {path} ({len(entries)} 项)\n" + "\n".join(entries)

    @staticmethod
    def glob_files(pattern: str, search_path: Optional[str] = None) -> str:
        """
        Glob 模式匹配文件

        参数:
            pattern: glob 模式，如 "**/*.py"
            search_path: 搜索目录（默认工作目录）

        返回:
            匹配的文件列表
        """
        import glob as glob_module

        base = search_path if search_path else config.workspace_root or "."
        base_path = safe_path(base, config.workspace_root)

        matches = sorted(glob_module.glob(pattern, root_dir=base_path, recursive=True))

        if not matches:
            return f"未找到匹配 '{pattern}' 的文件"

        lines = [f"匹配 '{pattern}' 的文件 ({len(matches)} 个):"]
        for m in matches:
            full = base_path / m
            size = full.stat().st_size if full.is_file() else 0
            lines.append(
                f"  {m} ({size / 1024:.1f} KB)" if full.is_file() else f"  {m}/"
            )

        return "\n".join(lines)

    @staticmethod
    def get_file_info(file_path: str) -> str:
        """获取文件信息"""
        path = safe_path(file_path, config.workspace_root)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        stat = path.stat()
        is_dir = path.is_dir()

        lines = [
            f"路径: {path.resolve()}",
            f"类型: {'目录' if is_dir else '文件'}",
            f"大小: {stat.st_size / 1024:.1f} KB" if not is_dir else "-",
            f"创建时间: {stat.st_ctime}",
            f"修改时间: {stat.st_mtime}",
        ]
        return "\n".join(lines)
