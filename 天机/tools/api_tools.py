"""
天机 - 外部 API 调用工具
通用 REST API 客户端
"""

import json
from typing import Optional

import requests

from ..utils.helpers import setup_logger

logger = setup_logger("天机.APITools")


class APITools:
    """外部 API 调用工具"""

    @staticmethod
    def call_api(
        method: str,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        data: Optional[str] = None,
        timeout: int = 30,
    ) -> str:
        """
        调用外部 REST API

        参数:
            method: HTTP 方法 (GET/POST/PUT/DELETE/PATCH)
            url: API 地址
            headers: 请求头
            params: URL 查询参数
            json_data: JSON 请求体
            data: 原始请求体（当 json_data 不适用时）
            timeout: 超时秒数

        返回:
            API 响应内容
        """
        method = method.upper()
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
        if method not in valid_methods:
            return (
                f"[错误] 不支持的 HTTP 方法: {method}，可用: {', '.join(valid_methods)}"
            )

        # 默认请求头
        req_headers = {
            "User-Agent": "Tianji-Agent/0.1",
        }
        if headers:
            req_headers.update(headers)

        logger.info(f"API {method} {url}")

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=req_headers,
                params=params,
                json=json_data,
                data=data,
                timeout=timeout,
            )

            # 尝试格式化 JSON 响应
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = resp.json()
                    formatted = json.dumps(body, ensure_ascii=False, indent=2)
                    return (
                        f"HTTP {resp.status_code} ({len(resp.content)} bytes)\n"
                        f"{formatted}"
                    )
                except json.JSONDecodeError:
                    pass

            # 非 JSON 响应
            body = resp.text
            max_len = 10000
            if len(body) > max_len:
                body = body[:max_len] + (f"\n... [截断，共 {len(body)} 字符]")

            return f"HTTP {resp.status_code} ({len(resp.content)} bytes)\n{body}"

        except requests.RequestException as e:
            return f"[错误] API 请求失败: {e}"
        except Exception as e:
            return f"[错误] 处理失败: {e}"
