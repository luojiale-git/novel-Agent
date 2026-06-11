import json
import re
import traceback
from typing import Iterator, Optional
from .llm import get_llm, LLMBackend
from .tools import ToolRegistry

SYSTEM_PROMPT = """你是「灵枢」- 天机桌面版的 AI 智能体，一个全能的创作助手。

## 核心原则
1. **主动分析** - 分析用户需求，制定执行计划
2. **工具使用** - 需要时调用工具，不需要时直接回复
3. **创作辅助** - 帮助用户写作、研究、编码、分析
4. **简洁有效** - 用最少的步骤完成任务

## 工作流程
1. 分析用户需求
2. 如果需要工具，调用 <function_call> 标签
3. 观察工具返回结果
4. 继续思考或给出最终回复

{tool_descriptions}
"""


class ConversationMemory:
    def __init__(self, max_turns: int = 20):
        self.messages: list[dict] = []
        self.max_turns = max_turns
        self.system_prompt = ""

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    def add_tool_message(self, content: str):
        self.messages.append({"role": "tool", "content": content})
        self._trim()

    def get_api_messages(self) -> list[dict]:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.messages)
        return msgs

    def _trim(self):
        while len(self.messages) > self.max_turns * 2:
            self.messages.pop(0)

    def reset(self):
        self.messages = []

    def to_dict(self) -> dict:
        return {"messages": self.messages, "system_prompt": self.system_prompt}

    def from_dict(self, data: dict):
        self.messages = data.get("messages", [])
        self.system_prompt = data.get("system_prompt", "")


class Agent:
    def __init__(self, llm_backend: Optional[str] = None):
        self.llm = get_llm(llm_backend)
        self.memory = ConversationMemory()
        self.tools = ToolRegistry()
        self.max_iterations = 10

    def _build_system_prompt(self) -> str:
        return SYSTEM_PROMPT.replace(
            "{tool_descriptions}", self.tools.get_tool_descriptions()
        )

    def _parse_function_call(self, text: str) -> Optional[dict]:
        pattern = r"<function_call>\s*(.*?)\s*</function_call>"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                return None
        return None

    def _extract_reasoning(self, response: str, func_call: dict) -> str:
        pattern = r"<function_call>.*?</function_call>"
        reasoning = re.sub(pattern, "", response, flags=re.DOTALL).strip()
        return reasoning if reasoning else ""

    def run_stream(self, user_input: str) -> Iterator[tuple[str, str]]:
        """流式运行 ReAct 循环。yield (type, content) 对"""
        if len(self.memory.messages) == 0:
            self.memory.set_system_prompt(self._build_system_prompt())

        self.memory.add_user_message(user_input)
        yield "reasoning", f"分析: {user_input[:50]}..."

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            yield "reasoning", f"思考 (第{iteration}轮)..."

            try:
                response = self.llm.chat(self.memory.get_api_messages(), stream=False)
            except Exception as e:
                yield "error", f"LLM 调用失败: {e}"
                break

            func_call = self._parse_function_call(response)

            if func_call:
                reasoning = self._extract_reasoning(response, func_call)
                if reasoning:
                    yield "reasoning", reasoning

                tool_name = func_call.get("name", "")
                arguments = func_call.get("arguments", {})

                yield (
                    "tool_call",
                    json.dumps(
                        {"tool": tool_name, "arguments": arguments}, ensure_ascii=False
                    ),
                )

                self.memory.add_assistant_message(response)

                tool = self.tools.get(tool_name)
                if tool:
                    try:
                        result = tool.fn(**arguments)
                        result_str = str(result)[:3000]
                        yield "observation", result_str
                        self.memory.add_tool_message(
                            f"工具 {tool_name} 返回: {result_str}"
                        )
                    except Exception as e:
                        err = f"工具执行错误: {e}\n{traceback.format_exc()}"
                        yield "error", err
                        self.memory.add_tool_message(err)
                else:
                    err = f"未知工具: {tool_name}"
                    yield "error", err
                    self.memory.add_tool_message(err)
            else:
                yield "response", response
                self.memory.add_assistant_message(response)
                return

        if iteration >= self.max_iterations:
            yield "response", "已达到最大迭代次数，请简化问题或重试。"

    def run(self, user_input: str) -> str:
        full = ""
        for event_type, content in self.run_stream(user_input):
            if event_type == "response":
                full += content
        return full

    def reset(self):
        self.memory.reset()

    def get_memory_state(self) -> dict:
        return self.memory.to_dict()

    def load_memory_state(self, state: dict):
        self.memory.from_dict(state)
