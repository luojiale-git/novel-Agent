from typing import Any, Callable, Optional
import os
import json
import glob as glob_mod
import re
import requests
from urllib.parse import urlparse
import shutil


class ToolDefinition:
    def __init__(self, name: str, fn: Callable, description: str = "", parameters: dict = None):
        self.name = name
        self.fn = fn
        self.description = description
        self.parameters = parameters or {}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认工具集"""
        self.register(ToolDefinition("read_file", self._read_file, "读取文件内容", {
            "path": {"type": "string", "description": "文件路径"}
        }))
        self.register(ToolDefinition("write_file", self._write_file, "写入文件内容", {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"}
        }))
        self.register(ToolDefinition("list_files", self._list_files, "列出目录文件", {
            "path": {"type": "string", "description": "目录路径"}
        }))
        self.register(ToolDefinition("web_search", self._web_search, "搜索网络信息", {
            "query": {"type": "string", "description": "搜索关键词"}
        }))
        self.register(ToolDefinition("read_project_doc", self._read_project_doc, "读取项目文档", {
            "project_id": {"type": "string", "description": "项目ID"},
            "doc_id": {"type": "string", "description": "文档ID"}
        }))
        self.register(ToolDefinition("write_project_doc", self._write_project_doc, "写入项目文档", {
            "project_id": {"type": "string", "description": "项目ID"},
            "title": {"type": "string", "description": "文档标题"},
            "content": {"type": "string", "description": "文档内容"},
            "doc_type": {"type": "string", "description": "文档类型"}
        }))

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [{"name": t.name, "description": t.description, "parameters": t.parameters} for t in self._tools.values()]

    def get_tool_descriptions(self) -> str:
        """生成工具描述文本供LLM使用"""
        lines = ["\n# 可用工具\n"]
        for t in self._tools.values():
            lines.append(f"- **{t.name}**: {t.description}")
            if t.parameters:
                param_lines = [
                    f"  - `{k}` ({v.get('type', 'string')}): {v.get('description', '')}"
                    for k, v in t.parameters.items()
                ]
                lines.extend(param_lines)
        lines.append("""
调用格式：
<function_call>
{"name": "工具名", "arguments": {"参数": "值"}}
</function_call>
""")
        return "\n".join(lines)

    # ---- 工具实现 ----

    def _read_file(self, path: str = "") -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"错误: {e}"

    def _write_file(self, path: str = "", content: str = "") -> str:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"已写入 {path}"
        except Exception as e:
            return f"错误: {e}"

    def _list_files(self, path: str = "") -> str:
        try:
            files = os.listdir(path)
            return "\n".join(files)
        except Exception as e:
            return f"错误: {e}"

    def _web_search(self, query: str = "") -> str:
        try:
            resp = requests.get(
                f"https://api.duckduckgo.com/?q={query}&format=json",
                timeout=10
            )
            data = resp.json()
            results = []
            for topic in data.get("RelatedTopics", [])[:5]:
                if "Text" in topic:
                    results.append(f"- {topic.get('Text', '')}")
            return "\n".join(results) if results else "未找到相关信息"
        except Exception as e:
            return f"搜索失败: {e}"

    def _read_project_doc(self, project_id: str = "", doc_id: str = "") -> str:
        """需要外部注入，此处为占位"""
        return f"文档 {doc_id} 属于项目 {project_id}"

    def _write_project_doc(self, project_id: str = "", title: str = "",
                           content: str = "", doc_type: str = "note") -> str:
        return f"已创建文档: {title}"

    def __len__(self):
        return len(self._tools)
