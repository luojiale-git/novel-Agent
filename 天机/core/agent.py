"""
天机 - 智能体核心调度引擎
ReAct 循环：思考 → 调用工具 → 观察 → 思考 ...
"""

import json
import re
import traceback
from typing import Any, Callable, Optional

from ..config import config
from ..utils.helpers import setup_logger, truncate_text
from .llm import get_llm, LLMBackend
from .memory import ConversationMemory
from .. import tools

logger = setup_logger("天机.Agent")


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self, name: str, fn: Callable, description: str = "", category: str = "general"
    ):
        """注册一个工具"""
        self._tools[name] = {
            "name": name,
            "function": fn,
            "description": description,
            "category": category,
        }
        logger.debug(f"注册工具: {name}")

    def get(self, name: str) -> Optional[Callable]:
        """获取工具函数"""
        tool = self._tools.get(name)
        return tool["function"] if tool else None

    def list_tools(self) -> list[dict]:
        """列出所有可用工具"""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
            }
            for t in self._tools.values()
        ]

    def get_tool_descriptions(self) -> str:
        """生成工具说明文本（注入系统提示词）"""
        lines = ["\n## 可用工具\n"]
        categories = {}
        for t in self._tools.values():
            cat = t["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(t)

        for cat, tools_list in categories.items():
            lines.append(f"\n### {cat}")
            for t in tools_list:
                lines.append(f"- **{t['name']}**: {t['description']}")

        lines.append("""

调用工具时，请按以下格式回复：

工具调用格式：
<function_call>
{"name": "工具名", "arguments": {"参数1": "值1", "参数2": "值2"}}
</function_call>

注意：
1. 一次只能调用一个工具
2. 调用工具后，会返回观察结果
3. 根据观察结果继续思考
4. 不需要工具时，直接回复最终答案
""")
        return "\n".join(lines)

    def auto_register_module(self, module, category: str = "general"):
        """自动扫描模块中带有 @tool 装饰器的函数并注册"""
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if hasattr(obj, "_tool_name") and obj._tool_name:
                self.register(
                    name=obj._tool_name,
                    fn=obj,
                    description=getattr(obj, "_tool_description", ""),
                    category=category,
                )

    def __len__(self):
        return len(self._tools)


# 系统提示词模板
SYSTEM_PROMPT = """你是「天机」，一个全能的自动化智能体。

## 核心原则
1. **自主性** - 主动分析任务、拆解步骤、选择合适工具
2. **准确性** - 执行操作前确认参数，执行后验证结果
3. **安全性** - 不执行破坏性操作（除非用户明确要求）
4. **简洁性** - 用最少的步骤完成任务

## 工作流程
1. 分析用户需求，制定执行计划
2. 按计划调用工具
3. 观察工具执行结果
4. 根据结果决定下一步行动
5. 任务完成后，向用户总结结果

{function_list}

## 回复格式
- 需要调用工具时，使用 <function_call> 标签
- 不需要调用工具时，直接自然回复
- 始终使用和用户相同的语言回复
"""


from .tool_decorator import tool  # noqa: F401 — 保持兼容性


class Agent:
    """智能体主引擎"""

    def __init__(self, llm_backend: Optional[str] = None):
        self.llm: LLMBackend = get_llm(llm_backend)
        self.memory = ConversationMemory()
        self.tools = ToolRegistry()
        self.max_iterations = 10  # 单次任务最大工具调用次数
        self._register_default_tools()

    def _register_default_tools(self):
        """注册所有默认工具"""

        # ---- 文件操作 ----
        ft = tools.FileTools()
        self.tools.register(
            "read_file",
            ft.read_file,
            description="读取文件内容，支持指定行号和行数限制",
            category="文件操作",
        )
        self.tools.register(
            "write_file",
            ft.write_file,
            description="写入文件内容（不存在则创建）",
            category="文件操作",
        )
        self.tools.register(
            "edit_file",
            ft.edit_file,
            description="编辑文件中的指定文本（精确字符串替换）",
            category="文件操作",
        )
        self.tools.register(
            "list_directory",
            ft.list_directory,
            description="列出目录内容",
            category="文件操作",
        )
        self.tools.register(
            "glob_files",
            ft.glob_files,
            description="使用 glob 模式搜索文件",
            category="文件操作",
        )
        self.tools.register(
            "get_file_info",
            ft.get_file_info,
            description="获取文件或目录的详细信息",
            category="文件操作",
        )

        # ---- 代码搜索 ----
        ct = tools.CodeTools()
        self.tools.register(
            "grep",
            ct.grep,
            description="在文件中搜索匹配正则表达式的内容",
            category="代码搜索",
        )
        self.tools.register(
            "find_files",
            ct.find_files,
            description="按文件名模式查找文件",
            category="代码搜索",
        )

        # ---- 命令执行 ----
        st = tools.ShellTools()
        self.tools.register(
            "execute",
            st.execute,
            description="执行 Shell 命令",
            category="命令执行",
        )
        self.tools.register(
            "get_system_info",
            st.get_system_info,
            description="获取系统基本信息",
            category="命令执行",
        )

        # ---- 网络 ----
        wt = tools.WebTools()
        self.tools.register(
            "web_search",
            wt.web_search,
            description="进行网络搜索",
            category="网络",
        )
        self.tools.register(
            "fetch_url",
            wt.fetch_url,
            description="获取网页内容",
            category="网络",
        )

        # ---- 小说创作 ----
        try:
            from features.novel import tools as novel_tools

            self.tools.auto_register_module(novel_tools, category="小说创作")
        except ImportError as e:
            logger.warning(f"小说创作工具注册失败: {e}")

        # ---- API ----
        at = tools.APITools()
        self.tools.register(
            "call_api",
            at.call_api,
            description="调用外部 REST API",
            category="API",
        )

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        func_desc = self.tools.get_tool_descriptions()
        return SYSTEM_PROMPT.replace("{function_list}", func_desc)

    def run(self, user_input: str) -> str:
        """
        运行单次对话

        参数:
            user_input: 用户输入

        返回:
            最终回复
        """
        # 初始化系统提示词
        if len(self.memory) == 0:
            self.memory.set_system_prompt(self._build_system_prompt())

        # 添加用户消息
        self.memory.add_user_message(user_input)

        # ReAct 循环
        iteration = 0
        final_response = ""

        while iteration < self.max_iterations:
            iteration += 1

            # 调用 LLM
            try:
                response = self.llm.chat(self.memory.api_messages)
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                final_response = f"[错误] 与 AI 模型通信时出错: {e}"
                break

            # 检查是否包含 function_call
            func_call = self._parse_function_call(response)

            if func_call:
                # 记录推理过程
                reasoning = self._extract_reasoning(response, func_call)
                if reasoning:
                    logger.info(f"[思考] {reasoning}")

                # 执行工具调用
                logger.info(f"[工具] 调用工具: {func_call['name']}")
                self.memory.add_assistant_message(response)

                result = self._execute_tool(func_call)
                logger.info(f"[结果] 工具结果: {result[:200]}...")

                # 添加观察结果
                obs_msg = f"工具 {func_call['name']} 返回结果:\n{result}"
                self.memory.add_message("user", obs_msg)
            else:
                # 没有函数调用，这就是最终回复
                final_response = response
                self.memory.add_assistant_message(response)
                break

        if iteration >= self.max_iterations and not final_response:
            final_response = "[警告] 已达到最大迭代次数，任务可能未完成。如有需要，请告诉我继续处理。"

        return final_response

    def _parse_function_call(self, response: str) -> Optional[dict]:
        """从 LLM 回复中解析工具调用"""
        # 匹配 <function_call>...</function_call>
        pattern = r"<function_call>\s*(\{.*?\})\s*</function_call>"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            try:
                call_data = json.loads(match.group(1))
                if "name" in call_data:
                    return call_data
            except json.JSONDecodeError:
                logger.warning(f"解析 function_call JSON 失败: {match.group(1)}")
        return None

    def _extract_reasoning(self, full_response: str, func_call: dict) -> Optional[str]:
        """提取推理过程（function_call 之前的文本）"""
        pattern = r"(.*?)<function_call>"
        match = re.search(pattern, full_response, re.DOTALL)
        if match:
            text = match.group(1).strip()
            return text if text else None
        return None

    def _execute_tool(self, func_call: dict) -> str:
        """执行工具调用"""
        name = func_call.get("name", "")
        arguments = func_call.get("arguments", {})

        tool_fn = self.tools.get(name)
        if not tool_fn:
            return f"[错误] 未知工具: {name}，可用工具: {[t['name'] for t in self.tools.list_tools()]}"

        # 参数校验
        if not isinstance(arguments, dict):
            return f"[错误] 工具 {name} 的参数必须是字典类型"

        try:
            result = tool_fn(**arguments)
            return truncate_text(str(result), 5000)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"工具 {name} 执行失败:\n{tb}")
            return f"[错误] 工具 {name} 执行失败: {e}"

    def reset(self):
        """重置对话（保留系统提示词）"""
        self.memory.clear()
        logger.info("[重置] 对话已重置")

    def run_stream(self, user_input: str):
        """
        流式运行对话（逐步输出）

        这是一个生成器，逐步产出:
            ("reasoning", str)  - 推理过程
            ("function_call", dict) - 工具调用
            ("observation", str) - 观察结果
            ("response", str)   - 最终回复
        """
        if len(self.memory) == 0:
            self.memory.set_system_prompt(self._build_system_prompt())

        self.memory.add_user_message(user_input)

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.llm.chat(self.memory.api_messages)
            except Exception as e:
                yield ("error", str(e))
                return

            func_call = self._parse_function_call(response)

            if func_call:
                reasoning = self._extract_reasoning(response, func_call)
                if reasoning:
                    yield ("reasoning", reasoning)

                yield ("function_call", func_call)
                self.memory.add_assistant_message(response)

                result = self._execute_tool(func_call)
                yield ("observation", result)

                obs_msg = f"工具 {func_call['name']} 返回结果:\n{result}"
                self.memory.add_message("user", obs_msg)
            else:
                self.memory.add_assistant_message(response)
                yield ("response", response)
                return

        yield ("response", "[警告] 已达到最大迭代次数，任务可能未完成。")
