"""
小说 AI Agent 核心
- 生成大纲、写章节、续写、改写、扩写
- 支持 OpenAI 兼容 API（DeepSeek / OpenAI / 本地模型）
"""

import os
import json
from typing import Optional
import requests


# ------------------------------------------------------------------ #
# 系统提示词模板（网文专用）
# ------------------------------------------------------------------ #

SYSTEM_OUTLINE = """你是一个专业的网文小说大纲生成器。你擅长构建世界观、设计人物弧光和情节节奏。
请根据用户的设定，生成一份结构清晰的小说大纲，包括：
1. 故事背景/世界观
2. 主要人物介绍
3. 故事主线
4. 分卷/分幕结构（至少 5 章大纲）
请用中文输出，语言精炼有网文感。"""

SYSTEM_WRITE = """你是一个专业的网文小说写手。你的任务是根据用户提供的大纲、人物设定和章节概要，写出该章节的具体内容。
写作要求：
- 使用中文网文风格，语言流畅自然
- 注重对话、动作和场景描写
- 每章建议 2000-3000 字
- 保持人物性格一致性
- 在章节结尾留下钩子（悬念），吸引读者继续阅读
- 使用第三人称视角"""

SYSTEM_CONTINUE = """你是一个专业的网文小说写手。请根据上一章的内容，续写下一章。
写作要求：
- 延续上一章的风格和情节节奏
- 自然承接上一章的结尾悬念
- 每章约 2000-3000 字
- 使用第三人称视角
- 保持人物性格和叙事风格一致性"""

SYSTEM_REWRITE = """你是一个专业的网文小说编辑。请根据用户的要求，对给定的内容进行改写。
改写要求：
- 保持核心情节不变
- 按照用户的具体要求调整风格、视角或内容
- 提高文字质量和可读性
- 保持网文风格"""

SYSTEM_EXPAND = """你是一个专业的网文小说写手。请对用户给出的片段进行扩写。
扩写要求：
- 保留原有情节和风格
- 丰富细节描写（环境、心理、动作、对话）
- 让内容更加丰满生动
- 扩写后长度约为原来的 2-3 倍"""

SYSTEM_CHAT = """你是"网文趋势助手"，一个专注于网文行业的 AI 顾问。你的核心能力：

1. **网文趋势分析**：了解当前网文市场的热门题材、新兴流派和读者偏好
2. **题材推荐**：根据用户的需求和偏好，推荐适合的小说题材和方向
3. **创作建议**：提供作品定位、目标读者分析等专业建议
4. **市场洞察**：分析不同平台（起点、番茄、晋江等）的特点和热门品类

回答要求：
- 专业但不枯燥，用网文圈内人熟知的术语
- 涉及数据时给出具体的百分比或排名
- 推荐题材时说明理由和适用平台
- 保持友好、鼓励的语调"""

# 演示模式热门网文数据
DEMO_TRENDING_DATA = {
    "genres": [
        {
            "name": "玄幻",
            "heat": "🔥🔥🔥🔥🔥",
            "share": "35%",
            "trending_subgenres": ["诸天流", "重生流", "系统流", "无敌流", "神豪流"],
            "platforms": ["起点中文网", "创世中文网"],
            "reader_demo": "男性为主，18-30岁占比75%",
            "hot_titles": [
                "《诡秘之主》",
                "《牧神记》",
                "《大奉打更人》",
                "《道诡异仙》",
            ],
            "description": "长期占据网文最大市场份额，世界观宏大，升级体系清晰的作品最容易出圈",
        },
        {
            "name": "都市",
            "heat": "🔥🔥🔥🔥",
            "share": "20%",
            "trending_subgenres": [
                "都市异能",
                "豪门赘婿",
                "重生商战",
                "职场文",
                "电竞文",
            ],
            "platforms": ["番茄小说", "起点中文网"],
            "reader_demo": "男女通吃，25-35岁白领占比高",
            "hot_titles": ["《大王饶命》", "《全球高武》", "《修复师》"],
            "description": "代入感最强，贴近现实生活的题材持续受到欢迎",
        },
        {
            "name": "仙侠",
            "heat": "🔥🔥🔥🔥",
            "share": "15%",
            "trending_subgenres": ["凡人流", "修真文明", "神话重生", "蜀山剑侠"],
            "platforms": ["起点中文网", "纵横中文网"],
            "reader_demo": "男性为主，核心读者群稳定",
            "hot_titles": ["《凡人修仙传》", "《仙逆》", "《一剑独尊》"],
            "description": "经典题材，近年来创新融合趋势明显，仙侠+悬疑、仙侠+科幻等",
        },
        {
            "name": "科幻",
            "heat": "🔥🔥🔥",
            "share": "10%",
            "trending_subgenres": [
                "末世废土",
                "星际文明",
                "人工智能",
                "时空穿梭",
                "赛博朋克",
            ],
            "platforms": ["起点中文网", "豆瓣阅读"],
            "reader_demo": "男性为主，高学历读者占比最高",
            "hot_titles": ["《三体》", "《流浪地球》", "《黎明之剑》"],
            "description": "随着科幻影视剧火爆，市场关注度持续上升",
        },
        {
            "name": "悬疑",
            "heat": "🔥🔥🔥",
            "share": "8%",
            "trending_subgenres": [
                "刑侦探案",
                "民俗志怪",
                "无限流",
                "盗墓",
                "心理悬疑",
            ],
            "platforms": ["起点中文网", "番茄小说"],
            "reader_demo": "男女比例均衡，推理爱好者为主",
            "hot_titles": ["《盗墓笔记》", "《鬼吹灯》", "《我有一座冒险屋》"],
            "description": "短剧改编热门题材，节奏紧凑的作品特别受欢迎",
        },
        {
            "name": "言情",
            "heat": "🔥🔥🔥",
            "share": "7%",
            "trending_subgenres": [
                "甜宠文",
                "古代言情",
                "总裁文",
                "重生虐渣",
                "校园文",
            ],
            "platforms": ["晋江文学城", "番茄小说", "红袖添香"],
            "reader_demo": "女性为主，16-28岁占比85%",
            "hot_titles": ["《知否》", "《花千骨》", "《何以笙箫默》"],
            "description": "IP改编成功率最高的品类，影视化潜力大",
        },
        {
            "name": "历史",
            "heat": "🔥🔥🔥",
            "share": "5%",
            "trending_subgenres": ["架空历史", "三国", "唐朝", "宋韵", "民国风云"],
            "platforms": ["起点中文网", "纵横中文网"],
            "reader_demo": "男性为主，历史爱好者群体",
            "hot_titles": ["《回到明朝当王爷》", "《新宋》", "《赘婿》"],
            "description": "考据严谨+爽点密集的作品最容易出成绩",
        },
    ],
    "platform_tips": {
        "起点中文网": "男频大本营，适合长篇小说，偏好玄幻/仙侠/历史",
        "番茄小说": "免费阅读模式，流量大，适合节奏快、爽点密的都市/言情",
        "晋江文学城": "女频第一站，言情/耽美为主，IP孵化能力强",
        "创世中文网": "腾讯系，玄幻/都市为主，IP改编资源丰富",
        "纵横中文网": "老牌网站，历史/仙侠类读者粘性高",
        "豆瓣阅读": "文艺向，悬疑/科幻短篇有优势",
    },
    "trending_keywords": [
        "系统流",
        "重生",
        "穿越",
        "金手指",
        "扮猪吃虎",
        "甜宠",
        "双洁",
        "非典型",
        "群像",
        "慢热",
        "克苏鲁",
        "中式科幻",
        "民俗恐怖",
        "修仙+",
        "单元剧",
        "日常文",
        "轻小说化",
        "反套路",
    ],
    "hot_trends_2026": [
        "AI 辅助创作与人工润色的结合模式成为主流",
        "短剧改编权成为网文 IP 变现核心渠道",
        "中式科幻/民俗志怪类题材爆发式增长",
        "互动式/沉浸式小说开始兴起",
        "中短篇精品化趋势明显，30-50万字作品增多",
    ],
}


class NovelAgent:
    """小说 AI Agent，通过 LLM API 生成内容"""

    def __init__(self):
        self.api_key = os.getenv("NOVEL_API_KEY", "")
        self.api_base = os.getenv("NOVEL_API_BASE", "https://api.deepseek.com/v1")
        self.model = os.getenv("NOVEL_MODEL", "deepseek-chat")
        self.temperature = float(os.getenv("NOVEL_TEMPERATURE", "0.85"))
        self.max_tokens = int(os.getenv("NOVEL_MAX_TOKENS", "4096"))

    # ------------------------------------------------------------------ #
    # 核心请求方法
    # ------------------------------------------------------------------ #
    def _call_llm(
        self, system_prompt: str, user_prompt: str, stream: bool = False
    ) -> str:
        """调用 LLM API"""
        if not self.api_key:
            return "[提示] 请先设置 NOVEL_API_KEY 环境变量以启用 AI 生成功能。\n当前使用演示模式，实际内容将由 AI 生成。"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

        try:
            resp = requests.post(
                f"{self.api_base.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[生成失败] API 调用出错: {e}\n\n请检查网络连接和 API 配置。"

    def _build_context(self, story: dict) -> str:
        """构建故事的上下文信息，用于注入提示词"""
        chars = story.get("characters", [])
        char_text = (
            "\n".join(
                f"- {c['name']}（{c['role']}）：{c['traits']}"
                if c["traits"]
                else f"- {c['name']}（{c['role']}）"
                for c in chars
            )
            if chars
            else "（暂无详细人物设定）"
        )

        settings = story.get("settings", [])
        setting_text = (
            "\n".join(f"- {s['name']}：{s['description']}" for s in settings)
            if settings
            else "（暂无详细设定）"
        )

        chapters = story.get("chapters", [])
        latest_chapters = chapters[-3:] if len(chapters) >= 3 else chapters
        chapter_summary = (
            "\n".join(
                f"第{c['chapter_number']}章 {c['title']}（前200字：{c['content'][:200]}...）"
                for c in latest_chapters
                if c["content"]
            )
            if latest_chapters
            else "（尚未有已完成的章节）"
        )

        context = f"""【故事信息】
标题：{story["title"]}
类型：{story["genre"]}
简介：{story["description"]}

【大纲】
{story["outline"] or "（暂未设置大纲）"}

【人物设定】
{char_text}

【世界观/设定】
{setting_text}

【已有章节概要】
{chapter_summary}
"""
        return context

    # ------------------------------------------------------------------ #
    # 生成大纲
    # ------------------------------------------------------------------ #
    def generate_outline(self, story: dict, user_instructions: str = "") -> str:
        """根据故事信息和用户要求生成大纲"""
        context = self._build_context(story)
        prompt = f"""请为以下小说生成详细大纲：

{context}

用户的额外要求：
{user_instructions or "（无特殊要求，请自行发挥）"}

请输出完整的大纲。"""
        return self._call_llm(SYSTEM_OUTLINE, prompt)

    # ------------------------------------------------------------------ #
    # 写章节
    # ------------------------------------------------------------------ #
    def write_chapter(
        self, story: dict, chapter_title: str, chapter_summary: str = ""
    ) -> str:
        """根据故事信息和章节概要写一章"""
        context = self._build_context(story)
        prompt = f"""请根据以下信息写出新的一章：

{context}

【本章信息】
章节标题：{chapter_title}
{"章节概要：" + chapter_summary if chapter_summary else "（请根据大纲自行构思本章内容）"}

请写出这一章的完整内容（2000-3000 字）。"""
        return self._call_llm(SYSTEM_WRITE, prompt)

    # ------------------------------------------------------------------ #
    # 续写
    # ------------------------------------------------------------------ #
    def continue_chapter(self, story: dict, last_chapter_content: str) -> str:
        """根据上一章内容续写下一章"""
        context = self._build_context(story)
        prompt = f"""请根据以下上下文续写下一章：

{context}

【上一章内容】
{last_chapter_content[:3000]}

请续写下一章，自然地承接上一章结尾的悬念，保持风格一致，约 2000-3000 字。"""
        return self._call_llm(SYSTEM_CONTINUE, prompt)

    # ------------------------------------------------------------------ #
    # 改写
    # ------------------------------------------------------------------ #
    def rewrite_content(self, content: str, instructions: str) -> str:
        """根据要求改写内容"""
        prompt = f"""请对以下内容进行改写：

【原文】
{content}

【改写要求】
{instructions}

请输出改写后的完整内容。"""
        return self._call_llm(SYSTEM_REWRITE, prompt)

    # ------------------------------------------------------------------ #
    # 扩写
    # ------------------------------------------------------------------ #
    def expand_content(self, content: str) -> str:
        """扩写内容片段"""
        prompt = f"""请对以下片段进行扩写，使其更加丰满生动：

{content}

请输出扩写后的完整内容。"""
        return self._call_llm(SYSTEM_EXPAND, prompt)

    # ------------------------------------------------------------------ #
    # 聊天 / 网文趋势咨询
    # ------------------------------------------------------------------ #
    def chat(self, message: str) -> str:
        """与 AI 顾问对话，咨询网文趋势和题材推荐"""
        import json

        # 演示模式：使用内置的热门数据生成回答
        if not self.api_key:
            return self._demo_chat(message)

        # 真实模式：调用 LLM 并注入趋势数据作为上下文
        trend_context = json.dumps(DEMO_TRENDING_DATA, ensure_ascii=False, indent=2)
        prompt = f"""当前网文市场热门数据（JSON）：
{trend_context}

用户咨询内容：
{message}

请基于以上市场数据，结合你的专业知识，给出有针对性的回答。"""

        return self._call_llm(SYSTEM_CHAT, prompt)

    def _demo_chat(self, message: str) -> str:
        """演示模式下的对话回复"""
        msg_lower = message.lower()

        # 热门题材推荐
        if any(
            kw in msg_lower
            for kw in ["热门", "推荐", "什么题材", "写什么", "流行", "趋势", "热门题材"]
        ):
            return self._build_genre_recommendation()

        # 特定类型询问
        genre_names = [g["name"] for g in DEMO_TRENDING_DATA["genres"]]
        for g in genre_names:
            if g in message:
                return self._build_genre_detail(g)

        # 平台建议
        if any(
            kw in msg_lower for kw in ["平台", "起点", "番茄", "晋江", "哪里发", "投稿"]
        ):
            return self._build_platform_advice()

        # 创作建议
        if any(
            kw in msg_lower for kw in ["创作", "写作", "建议", "新手", "入门", "技巧"]
        ):
            return self._build_writing_advice()

        # 默认回复
        return self._build_default_response()

    def _build_genre_recommendation(self) -> str:
        """生成热门题材推荐回复"""
        lines = [
            "## 📊 当前网文市场热门题材分析\n",
            "根据最新市场数据，以下是各题材的热度分布：\n",
        ]

        for g in DEMO_TRENDING_DATA["genres"]:
            lines.append(
                f"- **{g['name']}** {g['heat']} 占比 {g['share']}\n"
                f"  热门子类：{'、'.join(g['trending_subgenres'])}\n"
                f"  推荐平台：{'、'.join(g['platforms'])}\n"
            )

        lines.append("\n### 🏆 综合推荐\n")
        lines.append(
            "如果你是新手作者，建议优先考虑以下方向：\n\n"
            "1. **玄幻/诸天流** — 市场最大、读者最多，开篇容易出彩\n"
            "2. **都市/重生文** — 代入感强，短剧改编潜力大\n"
            "3. **悬疑/民俗志怪** — 2026年新兴热点，竞争相对小\n\n"
            "> 选择题材时，请结合你擅长的风格和了解的领域，"
            "热门赛道竞争也最激烈，差异化才是制胜关键。"
        )

        # 2026 趋势
        lines.append("\n### 🔮 2026 年趋势展望\n")
        for t in DEMO_TRENDING_DATA["hot_trends_2026"]:
            lines.append(f"- {t}")

        return "\n".join(lines)

    def _build_genre_detail(self, genre_name: str) -> str:
        """生成特定类型详情回复"""
        for g in DEMO_TRENDING_DATA["genres"]:
            if g["name"] == genre_name:
                lines = [
                    f"## {g['name']}类题材深度分析\n",
                    f"- **当前热度**：{g['heat']}\n",
                    f"- **市场份额**：{g['share']}\n",
                    f"- **热门子类**：{'、'.join(g['trending_subgenres'])}\n",
                    f"- **推荐平台**：{'、'.join(g['platforms'])}\n",
                    f"- **读者画像**：{g['reader_demo']}\n",
                    f"- **代表作品**：{'、'.join(g['hot_titles'])}\n",
                    f"- **特点分析**：{g['description']}\n",
                ]
                # 热门关键词
                lines.append("\n### 💡 创作关键词\n")
                lines.append(f"{'、'.join(DEMO_TRENDING_DATA['trending_keywords'])}\n")
                lines.append(
                    "\n> 建议在创作时融入2-3个热门关键词元素，提高作品曝光度。"
                )
                return "\n".join(lines)
        return f"抱歉，我暂时没有关于「{genre_name}」的详细数据。"

    def _build_platform_advice(self) -> str:
        """生成平台建议回复"""
        lines = ["## 📱 网文平台选择指南\n"]
        for name, desc in DEMO_TRENDING_DATA["platform_tips"].items():
            lines.append(f"- **{name}**：{desc}")
        lines.append("\n### 💡 建议\n")
        lines.append(
            "- **新手优先选择**：番茄小说（流量大、门槛低）或起点中文网（生态完善）\n"
            "- **女频作者**：首选晋江文学城，IP 孵化能力强\n"
            "- **多平台分发**：可以主站+免费阅读平台组合策略\n"
            "- **签约注意事项**：仔细阅读合同条款，特别是版权归属和分成比例"
        )
        return "\n".join(lines)

    def _build_writing_advice(self) -> str:
        """生成创作建议回复"""
        lines = [
            "## ✍️ 网文创作实用建议\n",
            "### 📌 开篇黄金法则\n",
            "1. **前三章定生死** — 编辑和读者都看前三章决定去留\n"
            "2. **第一句话要有钩子** — 制造悬念或冲突\n"
            "3. **快速建立期待** — 让读者知道这本书的「看点」是什么\n"
            "4. **章节结尾留悬念** — 每章结尾都要让读者想点下一章\n",
            "### 📈 数据化写作\n",
            "- 保持日更 4000-6000 字是及格线\n"
            "- 追读率 > 30% 算合格，> 50% 是有潜力\n"
            "- 黄金一章（第1章）的读完率决定推荐量\n"
            "- 标签和简介会影响平台推荐算法的匹配度\n",
            "### 🚀 新人避坑\n",
            "1. **不要开局设定大段世界观** — 要在情节中自然展现\n"
            "2. **不要慢热** — 网文读者耐心有限\n"
            "3. **不要频繁切换视角** — 新手建议保持单一主角视角\n"
            "4. **不要在开篇出现太多人物** — 读者记不住\n"
            "5. **不要忽视标题和简介** — 这是你的「封面」\n",
            "### 🤖 AI 辅助创作\n",
            "你可以使用本系统的 AI 功能来：\n"
            "- 生成故事大纲和世界设定\n"
            "- 辅助写章节、续写和扩写\n"
            "- 头脑风暴情节走向\n",
            "> 记住：AI 是你的写作伙伴，不是替代者。"
            " 最好的作品是「人类创意 + AI 效率」的结合。",
        ]
        return "\n".join(lines)

    def _build_default_response(self) -> str:
        """生成默认回复"""
        lines = [
            "## 👋 你好！我是网文趋势助手\n",
            "我可以帮你：\n",
            "1. **📊 热门题材推荐** — 了解当前什么题材最火\n"
            "2. **🔍 特定类型分析** — 比如输入「玄幻」「悬疑」了解详情\n"
            "3. **📱 平台选择建议** — 帮你选择适合的发表平台\n"
            "4. **✍️ 创作技巧** — 新人写作避坑指南\n"
            "5. **💡 趋势洞察** — 2026年网文市场新动向\n",
            "---\n",
            "试试问我：\n"
            "> 「现在什么题材最热门？」\n"
            "> 「我想写玄幻小说」\n"
            "> 「新手适合在哪个平台发表？」\n"
            "> 「给我一些写作建议」",
        ]
        return "\n".join(lines)
