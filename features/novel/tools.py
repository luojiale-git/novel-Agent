"""
小说创作工具 — 注册到天机 Agent 的 ToolRegistry

提供写作相关工具函数，覆盖统一数据模型全部字段。
"""

from 天机.core.agent import tool
from . import manager


@tool(
    name="novel_create_story",
    description="创建一个新故事，返回故事 ID",
    parameters={
        "title": {"type": "string", "description": "故事标题"},
        "genre": {"type": "string", "description": "故事类型/体裁"},
        "description": {"type": "string", "description": "故事简介"},
        "author": {"type": "string", "description": "作者"},
        "tone": {
            "type": "string",
            "description": "故事基调（如：悬疑/温馨/黑暗/幽默）",
        },
        "pov": {"type": "string", "description": "叙事视角（第一人称/第三人称等）"},
        "target_audience": {"type": "string", "description": "目标读者群体"},
        "tags": {"type": "string", "description": "标签，逗号分隔"},
    },
)
def create_story(
    title: str,
    genre: str = "",
    description: str = "",
    author: str = "",
    tone: str = "",
    pov: str = "",
    target_audience: str = "",
    tags: str = "",
) -> str:
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    story = manager.create_story(
        title=title,
        genre=genre,
        description=description,
        author=author,
        tone=tone,
        pov=pov,
        target_audience=target_audience,
        tags=tag_list,
    )
    return f"故事《{story['title']}》创建成功！ID: {story['id']}"


@tool(
    name="novel_list_stories",
    description="列出所有已创建的故事",
    parameters={},
)
def list_stories() -> str:
    stories = manager.list_stories()
    if not stories:
        return "暂无故事，使用 novel_create_story 创建一个吧。"
    lines = ["## 已有故事\n"]
    for s in stories:
        line = f"- **{s['title']}** (ID: {s['id']})"
        if s.get("genre"):
            line += f" [{s['genre']}]"
        if s.get("author"):
            line += f" by {s['author']}"
        if s.get("status"):
            line += f" ({s['status']})"
        if s.get("chapter_count", 0) > 0:
            line += f" — {s['chapter_count']}章"
        if s.get("tags"):
            line += f" 标签: {' '.join(s['tags'])}"
        lines.append(line)
    return "\n".join(lines)


@tool(
    name="novel_get_story",
    description="获取故事详情，包括人物、章节、世界观等信息",
    parameters={
        "story_id": {"type": "string", "description": "故事 ID"},
    },
)
def get_story(story_id: str) -> str:
    story = manager.get_story(story_id)
    if not story:
        return f"未找到故事 (ID: {story_id})"
    lines = [
        f"## {story['title']}",
        f"**类型**: {story.get('genre', '未设置')}",
    ]
    if story.get("author"):
        lines.append(f"**作者**: {story['author']}")
    if story.get("status"):
        lines.append(f"**状态**: {story['status']}")
    if story.get("tone"):
        lines.append(f"**基调**: {story['tone']}")
    if story.get("pov"):
        lines.append(f"**视角**: {story['pov']}")
    if story.get("target_audience"):
        lines.append(f"**目标读者**: {story['target_audience']}")
    if story.get("tags"):
        lines.append(f"**标签**: {' '.join(story['tags'])}")
    lines.append(f"**简介**: {story.get('description', '无')}")
    lines.append(f"**大纲**: {(story.get('outline') or '未设置')[:200]}")
    lines.append("")

    # 世界观
    world = story.get("world", {})
    if world.get("name") or world.get("description"):
        lines.append(f"### 世界观: {world.get('name', '未命名')}")
        if world.get("description"):
            lines.append(f"  描述: {world['description'][:200]}")
        if world.get("dimensions"):
            for d in world["dimensions"]:
                lines.append(f"  - {d.get('name')}: {d.get('description', '')[:80]}")
        lines.append("")

    # 人物
    chars = story.get("characters", [])
    lines.append(f"### 人物 ({len(chars)}人)")
    for c in chars:
        parts = [f"- {c['name']}"]
        if c.get("role"):
            parts.append(f"({c['role']})")
        if c.get("traits"):
            parts.append(f"[{c['traits']}]")
        if c.get("appearance"):
            parts.append(f"外貌: {c['appearance'][:60]}")
        if c.get("arc"):
            parts.append(f"成长: {c['arc'][:60]}")
        lines.append(" ".join(parts))
    lines.append("")

    # 章节
    chapters = story.get("chapters", [])
    lines.append(f"### 章节 ({len(chapters)}章)")
    total_words = sum(ch.get("word_count", 0) for ch in chapters)
    for ch in chapters:
        preview = (ch.get("content") or "")[:60].replace("\n", " ")
        status_tag = f"[{ch.get('status', 'draft')}]" if ch.get("status") else ""
        wc = ch.get("word_count", 0)
        lines.append(f"- {ch['title']} {status_tag} ({wc}字): {preview}...")
    lines.append(f"\n**总字数**: {total_words}")
    return "\n".join(lines)


@tool(
    name="novel_set_outline",
    description="设置或更新故事大纲",
    parameters={
        "story_id": {"type": "string", "description": "故事 ID"},
        "outline": {"type": "string", "description": "故事大纲内容"},
    },
)
def set_outline(story_id: str, outline: str) -> str:
    result = manager.update_story(story_id, outline=outline)
    if not result:
        return f"未找到故事 (ID: {story_id})"
    return f"故事大纲已更新！({len(outline)} 字)"


@tool(
    name="novel_add_chapter",
    description="为故事添加一个新章节",
    parameters={
        "story_id": {"type": "string", "description": "故事 ID"},
        "title": {"type": "string", "description": "章节标题"},
        "content": {"type": "string", "description": "章节正文"},
        "notes": {"type": "string", "description": "作者备注/写作笔记"},
        "status": {"type": "string", "description": "章节状态（draft/review/final）"},
    },
)
def add_chapter(
    story_id: str, title: str, content: str = "", notes: str = "", status: str = "draft"
) -> str:
    ch = manager.add_chapter(story_id, title, content, notes, status)
    if not ch:
        return f"未找到故事 (ID: {story_id})"
    return f"章节《{ch['title']}》已添加！(ID: {ch['id']}, {ch['word_count']}字)"


@tool(
    name="novel_update_chapter",
    description="更新指定章节的内容或属性",
    parameters={
        "story_id": {"type": "string", "description": "故事 ID"},
        "chapter_id": {"type": "string", "description": "章节 ID"},
        "title": {"type": "string", "description": "新标题"},
        "content": {"type": "string", "description": "新正文"},
        "notes": {"type": "string", "description": "作者备注"},
        "status": {"type": "string", "description": "章节状态（draft/review/final）"},
    },
)
def update_chapter(
    story_id: str,
    chapter_id: str,
    title: str = "",
    content: str = "",
    notes: str = "",
    status: str = "",
) -> str:
    kwargs = {}
    if title:
        kwargs["title"] = title
    if content:
        kwargs["content"] = content
    if notes:
        kwargs["notes"] = notes
    if status:
        kwargs["status"] = status
    if not kwargs:
        return "未提供任何更新字段。"
    ch = manager.update_chapter(story_id, chapter_id, **kwargs)
    if not ch:
        return f"未找到章节 (ID: {chapter_id})"
    return f"章节《{ch['title']}》已更新！({ch['word_count']}字, 状态: {ch['status']})"


@tool(
    name="novel_add_character",
    description="为故事添加一个人物",
    parameters={
        "story_id": {"type": "string", "description": "故事 ID"},
        "name": {"type": "string", "description": "人物名称"},
        "role": {"type": "string", "description": "角色定位（主角/反派/配角等）"},
        "traits": {"type": "string", "description": "性格特征"},
        "background": {"type": "string", "description": "背景故事"},
        "appearance": {"type": "string", "description": "外貌描写"},
        "arc": {"type": "string", "description": "角色成长弧线"},
    },
)
def add_character(
    story_id: str,
    name: str,
    role: str = "",
    traits: str = "",
    background: str = "",
    appearance: str = "",
    arc: str = "",
) -> str:
    char = manager.add_character(
        story_id, name, role, traits, background, appearance, arc
    )
    if not char:
        return f"未找到故事 (ID: {story_id})"
    parts = [f"人物「{char['name']}」已添加！"]
    if char.get("role"):
        parts.append(f"角色: {char['role']}")
    if char.get("appearance"):
        parts.append(f"外貌: {char['appearance'][:50]}")
    if char.get("arc"):
        parts.append(f"成长: {char['arc'][:50]}")
    return " | ".join(parts)


@tool(
    name="novel_update_world",
    description="设置或更新故事的世界观设定",
    parameters={
        "story_id": {"type": "string", "description": "故事 ID"},
        "name": {"type": "string", "description": "世界观名称"},
        "description": {"type": "string", "description": "世界观描述"},
        "rules": {"type": "string", "description": "世界规则/特殊设定"},
        "background": {"type": "string", "description": "历史背景"},
    },
)
def update_world(
    story_id: str,
    name: str = "",
    description: str = "",
    rules: str = "",
    background: str = "",
) -> str:
    world = manager.update_world(
        story_id,
        name=name or None,
        description=description or None,
        rules=rules or None,
        background=background or None,
    )
    if not world:
        return f"未找到故事 (ID: {story_id})"
    return f"世界观「{world['name'] or '未命名'}」已更新！"


# 注册列表，供 Agent 自动发现
__all_tools__ = [
    create_story,
    list_stories,
    get_story,
    set_outline,
    add_chapter,
    update_chapter,
    add_character,
    update_world,
]
