"""
天机 - 网络工具
支持网页搜索和内容抓取
"""

from typing import Optional

import requests

from ..config import config
from ..utils.helpers import setup_logger

logger = setup_logger("天机.WebTools")


class WebTools:
    """网络搜索与抓取工具"""

    @staticmethod
    def web_search(query: str, num_results: Optional[int] = None) -> str:
        """
        网络搜索

        参数:
            query: 搜索关键词
            num_results: 返回结果数量

        返回:
            搜索结果文本
        """
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return (
                "[错误] 需要安装 duckduckgo_search 库。请运行: "
                "pip install duckduckgo_search"
            )

        max_results = num_results or config.web_search_max_results

        logger.info(f"搜索: {query}")

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            return f"[错误] 搜索失败: {e}"

        if not results:
            return f"未找到 '{query}' 的相关结果"

        output = [f"[搜索] 搜索结果: {query}\n"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "无标题")
            link = r.get("href", "")
            snippet = r.get("body", "")
            output.append(f"{i}. {title}")
            output.append(f"   链接: {link}")
            output.append(f"   摘要: {snippet[:200]}")
            output.append("")

        return "\n".join(output)

    @staticmethod
    def fetch_url(url: str, format: str = "markdown") -> str:
        """
        抓取 URL 内容

        参数:
            url: 网页地址
            format: 返回格式 (text/markdown/html)

        返回:
            网页内容
        """
        logger.info(f"抓取: {url}")

        try:
            resp = requests.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                },
                timeout=30,
            )
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            content = resp.text

            if format == "markdown" or format == "text":
                # 简单的 HTML 到文本转换
                if "text/html" in content_type:
                    from html.parser import HTMLParser

                    class TextExtractor(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.text_parts = []
                            self.skip_tag = False

                        def handle_starttag(self, tag, attrs):
                            if tag in ("script", "style"):
                                self.skip_tag = True
                            if tag in (
                                "p",
                                "br",
                                "div",
                                "h1",
                                "h2",
                                "h3",
                                "h4",
                                "h5",
                                "h6",
                                "li",
                                "tr",
                            ):
                                self.text_parts.append("\n")

                        def handle_endtag(self, tag):
                            if tag in ("script", "style"):
                                self.skip_tag = False

                        def handle_data(self, data):
                            if not self.skip_tag:
                                data = data.strip()
                                if data:
                                    self.text_parts.append(data + " ")

                    extractor = TextExtractor()
                    extractor.feed(content)
                    content = "".join(extractor.text_parts)
                    # 压缩空白
                    import re

                    content = re.sub(r"\n{3,}", "\n\n", content)
                    content = re.sub(r" {2,}", " ", content)

            # 截断
            max_len = 15000
            if len(content) > max_len:
                content = content[:max_len] + (
                    f"\n\n... [内容已截断，共 {len(content)} 字符，"
                    f"仅显示前 {max_len} 字符]"
                )

            return content

        except requests.RequestException as e:
            return f"[错误] 请求失败: {e}"
        except Exception as e:
            return f"[错误] 处理失败: {e}"
