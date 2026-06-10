"""
天机 - 辅助函数模块
"""

import re
import logging
from pathlib import Path
from typing import Optional


def setup_logger(name: str = "天机", level: Optional[str] = None) -> logging.Logger:
    """配置并返回日志器"""
    if level is None:
        from ..config import config

        level = config.log_level

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def safe_path(path_str: str, workspace_root: Optional[str] = None) -> Path:
    """
    安全解析路径，防止目录穿越攻击
    如果设置了 workspace_root，则限制路径必须在工作目录内
    """
    path = Path(path_str).resolve()

    if workspace_root:
        root = Path(workspace_root).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise PermissionError(f"路径 {path} 不在工作目录 {root} 内，操作被拒绝")

    return path


def truncate_text(text: str, max_length: int = 2000) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return (
        text[:max_length]
        + f"\n\n... [已截断，共 {len(text)} 字符，仅显示前 {max_length} 字符]"
    )


def parse_code_blocks(text: str) -> list[dict]:
    """解析文本中的代码块，返回 [{'language': str, 'code': str}, ...]"""
    pattern = r"```(\w*)\n(.*?)```"
    blocks = []
    for match in re.finditer(pattern, text, re.DOTALL):
        blocks.append(
            {
                "language": match.group(1) or "text",
                "code": match.group(2).strip(),
            }
        )
    return blocks
