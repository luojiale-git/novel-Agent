"""
@tool 装饰器 — 为函数附加工具元数据，供 ToolRegistry 自动注册使用。

独立模块以避免 agent.py ↔ tools.py 之间的循环导入。
"""

from typing import Callable


def tool(name: str = "", description: str = "", parameters: dict | None = None):
    """装饰器：为函数附加工具元数据，供 ToolRegistry 自动注册使用。

    用法:
        @tool(name="my_tool", description="做什么的", parameters={...})
        def my_tool_func(arg1: str, arg2: int):
            ...

    参数:
        name: 工具名（空时自动取函数名）
        description: 工具描述
        parameters: 参数 JSON schema 描述
    """

    def decorator(fn: Callable) -> Callable:
        fn._tool_name = name or fn.__name__  # type: ignore[attr-defined]
        fn._tool_description = description  # type: ignore[attr-defined]
        fn._tool_parameters = parameters or {}  # type: ignore[attr-defined]
        return fn

    return decorator
