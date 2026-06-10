#!/usr/bin/env python3
"""
天机 - CLI 入口
交互式 REPL 模式（默认） / 单次查询模式 (--query)
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

# 将项目父目录加入 sys.path，确保包导入正确
_project_parent = Path(__file__).resolve().parent.parent
if str(_project_parent) not in sys.path:
    sys.path.insert(0, str(_project_parent))

from 天机.core.agent import Agent
from 天机.core.llm import (
    DeepSeekBackend,
    OpenAIBackend,
    OllamaBackend,
)
from 天机.config import config
from 天机.utils.helpers import setup_logger

logger = setup_logger("天机.CLI")


# ── ANSI 颜色 ──────────────────────────────────────────────
class Style:
    """终端样式常量"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"

    # 前景色
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    RED = "\033[31m"
    WHITE = "\033[37m"
    BRIGHT_WHITE = "\033[97m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_GREEN = "\033[92m"
    GRAY = "\033[90m"

    # 背景色
    BG_DARK = "\033[40m"

    @classmethod
    def colored(cls, text: str, color: str, *mods: str) -> str:
        mod = "".join(mods)
        return f"{mod}{color}{text}{cls.RESET}"

    @classmethod
    def dim(cls, text: str) -> str:
        return f"{cls.DIM}{text}{cls.RESET}"

    @classmethod
    def bold(cls, text: str, color: str = "") -> str:
        return f"{cls.BOLD}{color}{text}{cls.RESET}"


# ── Banner ──────────────────────────────────────────────────
BANNER = rf"""
{Style.colored("╔══════════════════════════════════════════╗", Style.CYAN, Style.BOLD)}
{Style.colored("║", Style.CYAN, Style.BOLD)}        {Style.colored("天  机", Style.BRIGHT_CYAN, Style.BOLD)}        {Style.colored("║", Style.CYAN, Style.BOLD)}
{Style.colored("║", Style.CYAN, Style.BOLD)}   {Style.dim("TIANJI — AI 自动化智能体")}   {Style.colored("║", Style.CYAN, Style.BOLD)}
{Style.colored("╚══════════════════════════════════════════╝", Style.CYAN, Style.BOLD)}
"""

HELP_TEXT = f"""
{Style.bold("可用命令", Style.BRIGHT_CYAN)}:
  {Style.bold("/help")}       显示此帮助信息
  {Style.bold("/reset")}      重置对话记忆
  {Style.bold("/clear")}      清屏
  {Style.bold("/history")}    显示对话历史摘要
  {Style.bold("/tools")}      显示当前可用工具列表
  {Style.bold("/config")}     显示当前配置（隐藏 API Key）
  {Style.bold("/exit")}       退出程序

{Style.dim("提示: 直接输入问题开始对话，支持多行输入（空行结束）。")}
{Style.dim("按 Ctrl+C 或输入 /exit 退出。")}
"""


# ── 输出渲染 ────────────────────────────────────────────────
def _render_event(event_type: str, content: str):
    """根据事件类型渲染输出"""
    if event_type == "reasoning":
        # 推理过程 → 灰色斜体
        print(f"  {Style.dim(Style.ITALIC)}{content}{Style.RESET}")
    elif event_type == "tool_call":
        # 工具调用 → 黄色
        print(
            f"  {Style.colored('⚡', Style.YELLOW)} {Style.colored(content, Style.YELLOW, Style.ITALIC)}"
        )
    elif event_type == "observation":
        # 工具返回 → 蓝色缩进
        for line in content.strip().split("\n"):
            print(f"    {Style.colored('↳', Style.BLUE)} {Style.dim(line)}")
    elif event_type == "response":
        # 最终回复 → 正常输出（由外部控制换行）
        print(content, end="", flush=True)
    elif event_type == "error":
        print(f"\n{Style.colored('✖ 错误', Style.RED, Style.BOLD)}: {content}")


def _show_welcome():
    """显示欢迎信息"""
    print(BANNER)
    print(
        f"  {Style.dim('后端')}:   {Style.bold(config.llm_backend, Style.BRIGHT_GREEN)}"
    )
    print(
        f"  {Style.dim('模型')}:   {Style.bold(config.llm_model, Style.BRIGHT_GREEN)}"
    )
    print(
        f"  {Style.dim('记忆')}:   {Style.bold(f'{config.memory_max_turns} 轮', Style.BRIGHT_GREEN)}"
    )
    print()


# ── 交互式 REPL ─────────────────────────────────────────────
def _repl(agent: Agent):
    """交互式对话循环"""
    _show_welcome()
    print(HELP_TEXT)
    print(Style.colored("─" * 46, Style.DIM))

    while True:
        try:
            # 多行输入: 读取直到空行
            lines = []
            print(f"\n{Style.bold('你', Style.GREEN)} > ", end="", flush=True)
            first_line = input().strip()
            if first_line:
                lines.append(first_line)
                # 尝试读取更多行
                while True:
                    try:
                        line = input(f"  {Style.dim('...')} ")
                    except EOFError:
                        break
                    if line.strip() == "":
                        break
                    lines.append(line)

            user_input = "\n".join(lines).strip()
            if not user_input:
                continue

            # ── 内部命令 ──
            if user_input.startswith("/"):
                _handle_command(agent, user_input)
                continue

            # ── 正常对话 ──
            print(f"\n{Style.bold('天机', Style.BRIGHT_CYAN)} > ", end="", flush=True)
            full_response = ""
            try:
                for event_type, content in agent.run_stream(user_input):
                    if event_type == "response":
                        full_response += content
                    _render_event(event_type, content)
                print()  # 结尾换行
            except Exception as e:
                if full_response:
                    print()  # 确保换行
                _render_event("error", str(e))
                logger.exception("对话出错")

        except KeyboardInterrupt:
            print(f"\n{Style.colored('⏎ 已中断', Style.YELLOW)}")
            continue
        except EOFError:
            print()
            _do_exit(agent)


def _handle_command(agent: Agent, cmd: str):
    """处理内部命令"""
    parts = cmd.strip().split()
    command = parts[0].lower()

    if command == "/exit" or command == "/quit":
        _do_exit(agent)

    elif command == "/help":
        print(HELP_TEXT)

    elif command == "/clear" or command == "/cls":
        # 跨平台清屏
        os.system("cls" if os.name == "nt" else "clear")

    elif command == "/reset":
        agent.reset()
        print(f"\n{Style.colored('✓ 对话记忆已重置', Style.GREEN)}")

    elif command == "/history":
        memory = agent.memory
        if not memory.messages:
            print(f"\n{Style.dim('暂无对话历史')}")
            return

        print(
            f"\n{Style.bold('对话历史', Style.BRIGHT_CYAN)} ({len(memory.messages)} 条消息):"
        )
        # 简化显示: 只显示角色和消息摘要
        for i, msg in enumerate(memory.messages, 1):
            role = msg.get("role", "?")
            content = msg.get("content", "")
            summary = content[:80] + "..." if len(content) > 80 else content
            role_tag = {
                "user": Style.colored("你", Style.GREEN),
                "assistant": Style.colored("天机", Style.BRIGHT_CYAN),
                "system": Style.dim("系统"),
                "tool": Style.colored("工具", Style.YELLOW),
            }.get(role, Style.dim(role))
            print(f"  {Style.dim(f'#{i:02d}')} {role_tag}: {Style.dim(summary)}")
        print()

    elif command == "/tools":
        tools = agent.tools.list_tools()
        if not tools:
            print(f"\n{Style.dim('暂无可用工具')}")
            return
        print(f"\n{Style.bold('可用工具', Style.BRIGHT_CYAN)} ({len(tools)} 个):")
        for t in tools:
            print(
                f"  {Style.colored('·', Style.CYAN)} {Style.bold(t['name'])}: {Style.dim(t['description'])}"
            )
        print()

    elif command == "/config":
        safe = config.to_dict()
        print(f"\n{Style.bold('当前配置', Style.BRIGHT_CYAN)}:")
        _print_dict(safe, indent=2)
        print()

    else:
        print(
            f"\n{Style.colored('✖ 未知命令', Style.RED)}: {command}  （输入 /help 查看可用命令）"
        )


def _print_dict(d: dict, indent: int = 0):
    """递归打印字典"""
    prefix = " " * indent
    for key, value in d.items():
        if isinstance(value, dict):
            print(f"{prefix}{Style.bold(str(key), Style.BRIGHT_WHITE)}:")
            _print_dict(value, indent + 2)
        else:
            print(f"{prefix}{Style.dim(str(key) + ':')} {value}")


def _do_exit(agent: Agent):
    """退出程序"""
    print(f"\n{Style.colored('天机已关闭。再见！', Style.CYAN, Style.ITALIC)}")
    sys.exit(0)


# ── 单次查询模式 ────────────────────────────────────────────
def _single_query(agent: Agent, query: str):
    """执行单次查询并退出"""
    print(f"{Style.colored('查询', Style.GREEN)}: {query}")
    print(f"{Style.colored('─' * 46, Style.DIM)}")

    full_response = ""
    try:
        for event_type, content in agent.run_stream(query):
            if event_type == "response":
                full_response += content
                print(content, end="", flush=True)
            else:
                _render_event(event_type, content)
        print()
    except Exception as e:
        if full_response:
            print()
        _render_event("error", str(e))
        logger.exception("查询出错")


# ── 主入口 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="天机 — AI 自动化智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python -m 天机.main                   # 交互模式\n"
            "  python -m 天机.main --query '你好'     # 单次查询\n"
            "  python -m 天机.main -q '介绍一下自己'   # 单次查询（简写）\n"
            "  python -m 天机.main --backend ollama   # 指定后端启动\n"
        ),
    )
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        default=None,
        help="单次查询模式：直接传入问题，输出回复后退出",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        choices=["deepseek", "openai", "ollama"],
        help="强制指定 LLM 后端（覆盖配置文件）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="强制指定模型名称（覆盖配置文件）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="启用调试日志",
    )

    args = parser.parse_args()

    # 调试日志
    if args.debug:
        os.environ["TIANJI_LOG_LEVEL"] = "DEBUG"

    # 构造 Agent
    try:
        agent = _build_agent(args)
    except Exception as e:
        print(
            f"{Style.colored('✖ 初始化失败', Style.RED, Style.BOLD)}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 选择模式
    if args.query:
        _single_query(agent, args.query)
    else:
        try:
            _repl(agent)
        except Exception as e:
            print(
                f"\n{Style.colored('✖ 致命错误', Style.RED, Style.BOLD)}: {e}",
                file=sys.stderr,
            )
            sys.exit(1)


def _build_agent(args) -> Agent:
    """根据命令行参数和配置构造 Agent 实例"""
    backend_name = args.backend or config.llm_backend

    # 验证后端支持
    valid_backends = {"deepseek", "openai", "ollama"}
    if backend_name not in valid_backends:
        raise ValueError(
            f"不支持的 LLM 后端: {backend_name!r}。可选: {', '.join(sorted(valid_backends))}"
        )

    # 创建 Agent（内部通过 Factory 创建 LLM 实例）
    agent = Agent(llm_backend=backend_name)

    # 如果命令行指定了模型名称，覆盖它
    if args.model:
        agent.llm.model = args.model

    # 验证 API Key（DeepSeek / OpenAI 需要）
    if hasattr(agent.llm, "api_key") and not agent.llm.api_key:
        print(
            f"{Style.colored('⚠ 警告', Style.YELLOW, Style.BOLD)}: "
            f"{agent.llm.name} API Key 未配置。请设置环境变量或修改 config.yaml。",
            file=sys.stderr,
        )

    logger.info(
        "初始化 Agent: backend=%s, model=%s",
        agent.llm.name,
        getattr(agent.llm, "model", "unknown"),
    )
    return agent


if __name__ == "__main__":
    main()
