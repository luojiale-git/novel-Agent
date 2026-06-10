#!/usr/bin/env python3
"""
天机 - 自动化智能体 CLI 入口
"""

import sys
import os
import io
from pathlib import Path

# 确保项目根在导入路径中
sys.path.insert(0, str(Path(__file__).parent))

# Windows GBK 终端兼容：遇到无法编码的字符自动替换（如 emoji）
if sys.stdout.encoding and sys.stdout.encoding.upper() not in ("UTF-8", "UTF8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from 天机 import __version__, __app_name__
from 天机.config import config
from 天机.core.agent import Agent
from 天机.utils.helpers import setup_logger


def print_banner():
    """打印启动横幅"""
    banner = rf"""
    ╔══════════════════════════════════════╗
    ║     ____  _   _    _    ___  ____    ║
    ║    |_ _|/ \ | |  / \  |_ _|/ ___|   ║
    ║     | |/ _ \| | / _ \  | || |       ║
    ║     | |/ ___ \ |/ ___ \ | || |___   ║
    ║    |___/_/   \_/_/   \_\___|\____|   ║
    ║                                      ║
    ║    {__app_name__} v{__version__} - 自动化智能体      ║
    ║    后端: {config.llm_backend}/{config.llm_model}              ║
    ╚══════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = f"""
{__app_name__} v{__version__} - 自动化智能体

用法:
    python main.py                   启动交互式对话
    python main.py "你的问题"        单次执行模式
    python main.py --help            显示帮助

命令:
    /exit, /quit     退出程序
    /reset           重置对话历史
    /tools           列出可用工具
    /config          显示当前配置
    /help            显示帮助

环境变量:
    TIANJI_API_KEY      设置 API Key（优先级最高）
    DEEPSEEK_API_KEY    设置 DeepSeek API Key
    OPENAI_API_KEY      设置 OpenAI API Key
    TIANJI_LOG_LEVEL    日志级别 (DEBUG/INFO/WARNING/ERROR)
"""
    print(help_text)


def print_config():
    """打印当前配置"""
    import json

    cfg = config.to_dict()
    print("当前配置:")
    print(json.dumps(cfg, ensure_ascii=False, indent=2))


def interactive_mode(agent: Agent):
    """交互式 CLI 模式"""
    print_banner()
    print("输入 /help 查看命令 (/exit 退出)\n")

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n再见！")
            break

        if not user_input:
            continue

        # 处理内置命令
        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd in ("/exit", "/quit"):
                print("再见！")
                break
            elif cmd == "/reset":
                agent.reset()
                print("[重置] 对话已重置")
                continue
            elif cmd == "/tools":
                tools = agent.tools.list_tools()
                print(f"可用工具 ({len(tools)} 个):")
                for t in tools:
                    print(f"  [{t['category']}] {t['name']}: {t['description'][:60]}")
                continue
            elif cmd == "/config":
                print_config()
                continue
            elif cmd == "/help":
                print_help()
                continue
            else:
                print(f"未知命令: {user_input}")
                continue

        # 执行任务
        print("[天机] 思考中...")
        try:
            result = agent.run(user_input)
            print(f"\n[天机] {result}\n")
        except Exception as e:
            print(f"\n[错误] {e}\n")


def single_run_mode(agent: Agent, query: str):
    """单次执行模式"""
    print(f"[用户] {query}")
    print("[天机] 思考中...")
    try:
        result = agent.run(query)
        print(f"\n[天机] {result}")
    except Exception as e:
        print(f"\n[错误] {e}")
        sys.exit(1)


def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description=f"{__app_name__} - 自动化智能体",
        add_help=False,
    )
    parser.add_argument("query", nargs="?", help="单次执行的问题")
    parser.add_argument("--help", action="store_true", help="显示帮助")
    parser.add_argument("--version", action="store_true", help="显示版本")
    parser.add_argument("--backend", type=str, help="指定 LLM 后端")
    args = parser.parse_args()

    if args.help:
        print_help()
        return

    if args.version:
        print(f"{__app_name__} v{__version__}")
        return

    # 初始化
    agent = Agent(llm_backend=args.backend)

    if args.query:
        single_run_mode(agent, args.query)
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
