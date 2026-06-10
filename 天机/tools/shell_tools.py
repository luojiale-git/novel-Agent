"""
天机 - 命令执行工具
安全的子进程执行，含白名单校验、超时控制、输出截断
"""

import asyncio
import shlex
import subprocess
from pathlib import Path
from typing import Optional

from ..config import config
from ..utils.helpers import setup_logger

logger = setup_logger("天机.ShellTools")


class ShellTools:
    """命令执行工具"""

    @staticmethod
    def execute(
        command: str,
        workdir: Optional[str] = None,
        timeout: Optional[int] = None,
        description: str = "",
    ) -> str:
        """
        执行 shell 命令

        参数:
            command: 要执行的命令
            workdir: 工作目录（默认使用配置文件中的工作目录）
            timeout: 超时时间（秒），默认使用配置值
            description: 命令描述（日志用）

        返回:
            命令输出
        """
        # 安全校验
        ShellTools._check_command(command)

        # 工作目录
        cwd = None
        if workdir:
            cwd = Path(workdir).resolve()
            if not cwd.exists():
                raise FileNotFoundError(f"工作目录不存在: {cwd}")

        # 超时
        cmd_timeout = timeout or config.command_timeout

        logger.info(f"执行命令: {description or command[:80]}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=cmd_timeout,
                encoding="utf-8",
                errors="replace",
            )

            # 构建输出
            output_parts = []

            if result.stdout:
                output_parts.append(result.stdout)

            if result.stderr:
                output_parts.append(f"[STDERR]\n{result.stderr}")

            output = "".join(output_parts)

            # 截断过长的输出
            max_output = 10000
            if len(output) > max_output:
                output = output[:max_output] + (
                    f"\n\n... [输出已截断，共 {len(output)} 字符，"
                    f"仅显示前 {max_output} 字符]"
                )

            exit_code = result.returncode
            info = f"命令完成 (exit code: {exit_code})"

            if exit_code != 0:
                info += f" [失败]"

            return f"{info}\n{output}" if output else info

        except subprocess.TimeoutExpired:
            return f"[错误] 命令执行超时 ({cmd_timeout}秒): {command[:100]}"
        except Exception as e:
            return f"[错误] 命令执行失败: {e}"

    @staticmethod
    def execute_async(
        command: str, workdir: Optional[str] = None, timeout: Optional[int] = None
    ) -> str:
        """
        异步执行命令（不阻塞主循环）

        参数:
            同 execute()

        返回:
            任务已提交的确认信息
        """
        ShellTools._check_command(command)

        import threading

        results = []

        def _run():
            try:
                result = ShellTools.execute(command, workdir, timeout)
                results.append(result)
            except Exception as e:
                results.append(f"[错误] 异步执行失败: {e}")

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return f"[等待] 已提交异步执行: {command[:100]}"

    @staticmethod
    def _check_command(command: str):
        """
        检查命令是否符合安全策略
        """
        allowed = config.allowed_commands
        if not allowed:
            return  # 白名单为空则允许所有

        # 提取命令名
        cmd_name = shlex.split(command)[0] if command.strip() else ""

        if cmd_name and cmd_name not in allowed:
            raise PermissionError(
                f"命令 '{cmd_name}' 不在允许列表中。允许的命令: {', '.join(allowed)}"
            )

    @staticmethod
    def get_system_info() -> str:
        """获取系统基本信息"""
        import platform
        import os

        info = [
            f"系统: {platform.system()} {platform.release()}",
            f"架构: {platform.machine()}",
            f"Python: {platform.python_version()}",
            f"主机: {platform.node()}",
            f"当前目录: {Path.cwd()}",
            f"CPU: {os.cpu_count()} 核",
        ]
        return "\n".join(info)
