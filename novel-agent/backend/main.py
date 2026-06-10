"""
小说 AI Agent - FastAPI 后端服务
"""

import json
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from story_manager import StoryManager
from novel_agent import NovelAgent

# ------------------------------------------------------------------ #
# 全局实例
# ------------------------------------------------------------------ #
story_mgr = StoryManager()
agent = NovelAgent()


# ------------------------------------------------------------------ #
# 请求 / 响应模型
# ------------------------------------------------------------------ #
class StoryCreate(BaseModel):
    title: str
    genre: str = ""
    description: str = ""


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    outline: Optional[str] = None


class CharacterCreate(BaseModel):
    name: str
    role: str = ""
    traits: str = ""
    background: str = ""


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    traits: Optional[str] = None
    background: Optional[str] = None


class ChapterCreate(BaseModel):
    title: str
    content: str = ""


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class SettingCreate(BaseModel):
    name: str
    description: str = ""


# AI 请求模型
class OutlineRequest(BaseModel):
    story_id: str
    instructions: str = ""


class WriteChapterRequest(BaseModel):
    story_id: str
    chapter_title: str
    chapter_summary: str = ""


class ContinueRequest(BaseModel):
    story_id: str


class RewriteRequest(BaseModel):
    story_id: str
    chapter_id: str
    instructions: str


class ExpandRequest(BaseModel):
    story_id: str
    chapter_id: str


class ChatRequest(BaseModel):
    message: str


# ------------------------------------------------------------------ #
# 应用启动/关闭
# ------------------------------------------------------------------ #
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    print(f"[Novel Agent] API 已启动")
    print(f"   数据目录: {story_mgr.data_dir}")
    if agent.api_key:
        print(f"   AI 模型: {agent.model} @ {agent.api_base}")
    else:
        print(f"   [警告] NOVEL_API_KEY 未设置，AI 功能运行在演示模式")
    yield
    # 关闭时
    print("[Novel Agent] 服务已关闭")


app = FastAPI(title="Novel Agent API", version="1.0.0", lifespan=lifespan)

# CORS - 允许前端开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================== #
#  故事 API
# ================================================================== #
@app.get("/api/stories")
def list_stories():
    """获取故事列表"""
    return story_mgr.list_stories()


@app.post("/api/stories")
def create_story(body: StoryCreate):
    """创建新故事"""
    story = story_mgr.create_story(body.title, body.genre, body.description)
    return story


@app.get("/api/stories/{story_id}")
def get_story(story_id: str):
    """获取故事详情"""
    story = story_mgr.get_story(story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    return story


@app.put("/api/stories/{story_id}")
def update_story(story_id: str, body: StoryUpdate):
    """更新故事"""
    data = body.model_dump(exclude_none=True)
    story = story_mgr.update_story(story_id, **data)
    if not story:
        raise HTTPException(404, "故事不存在")
    return story


@app.delete("/api/stories/{story_id}")
def delete_story(story_id: str):
    """删除故事"""
    ok = story_mgr.delete_story(story_id)
    if not ok:
        raise HTTPException(404, "故事不存在")
    return {"ok": True}


# ================================================================== #
#  人物 API
# ================================================================== #
@app.get("/api/stories/{story_id}/characters")
def list_characters(story_id: str):
    """获取故事人物列表"""
    story = story_mgr.get_story(story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    return story["characters"]


@app.post("/api/stories/{story_id}/characters")
def add_character(story_id: str, body: CharacterCreate):
    """添加人物"""
    char = story_mgr.add_character(
        story_id, body.name, body.role, body.traits, body.background
    )
    if not char:
        raise HTTPException(404, "故事不存在")
    return char


@app.put("/api/stories/{story_id}/characters/{char_id}")
def update_character(story_id: str, char_id: str, body: CharacterUpdate):
    """更新人物"""
    data = body.model_dump(exclude_none=True)
    char = story_mgr.update_character(story_id, char_id, **data)
    if not char:
        raise HTTPException(404, "人物不存在")
    return char


@app.delete("/api/stories/{story_id}/characters/{char_id}")
def delete_character(story_id: str, char_id: str):
    """删除人物"""
    ok = story_mgr.delete_character(story_id, char_id)
    if not ok:
        raise HTTPException(404, "人物不存在")
    return {"ok": True}


# ================================================================== #
#  章节 API
# ================================================================== #
@app.get("/api/stories/{story_id}/chapters")
def list_chapters(story_id: str):
    """获取章节列表"""
    story = story_mgr.get_story(story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    return story["chapters"]


@app.post("/api/stories/{story_id}/chapters")
def add_chapter(story_id: str, body: ChapterCreate):
    """添加章节"""
    ch = story_mgr.add_chapter(story_id, body.title, body.content)
    if not ch:
        raise HTTPException(404, "故事不存在")
    return ch


@app.put("/api/chapters/{chapter_id}")
def update_chapter(chapter_id: str, body: ChapterUpdate, story_id: str = ""):
    """更新章节（需提供 story_id 查询参数）"""
    if not story_id:
        raise HTTPException(400, "请提供 story_id 查询参数")
    data = body.model_dump(exclude_none=True)
    ch = story_mgr.update_chapter(story_id, chapter_id, **data)
    if not ch:
        raise HTTPException(404, "章节不存在")
    return ch


@app.get("/api/stories/{story_id}/chapters/{chapter_id}")
def get_chapter(story_id: str, chapter_id: str):
    """获取单个章节"""
    ch = story_mgr.get_chapter(story_id, chapter_id)
    if not ch:
        raise HTTPException(404, "章节不存在")
    return ch


@app.delete("/api/stories/{story_id}/chapters/{chapter_id}")
def delete_chapter(story_id: str, chapter_id: str):
    """删除章节"""
    ok = story_mgr.delete_chapter(story_id, chapter_id)
    if not ok:
        raise HTTPException(404, "章节不存在")
    return {"ok": True}


# ================================================================== #
#  设定 API
# ================================================================== #
@app.get("/api/stories/{story_id}/settings")
def list_settings(story_id: str):
    """获取设定列表"""
    story = story_mgr.get_story(story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    return story["settings"]


@app.post("/api/stories/{story_id}/settings")
def add_setting(story_id: str, body: SettingCreate):
    """添加设定"""
    setting = story_mgr.add_setting(story_id, body.name, body.description)
    if not setting:
        raise HTTPException(404, "故事不存在")
    return setting


@app.delete("/api/stories/{story_id}/settings/{setting_id}")
def delete_setting(story_id: str, setting_id: str):
    """删除设定"""
    ok = story_mgr.delete_setting(story_id, setting_id)
    if not ok:
        raise HTTPException(404, "设定不存在")
    return {"ok": True}


# ================================================================== #
#  AI Agent API
# ================================================================== #
@app.post("/api/agent/generate-outline")
def generate_outline(body: OutlineRequest):
    """AI 生成故事大纲"""
    story = story_mgr.get_story(body.story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    result = agent.generate_outline(story, body.instructions)
    return {"content": result}


@app.post("/api/agent/write-chapter")
def write_chapter(body: WriteChapterRequest):
    """AI 写一章"""
    story = story_mgr.get_story(body.story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    result = agent.write_chapter(story, body.chapter_title, body.chapter_summary)
    return {"content": result}


@app.post("/api/agent/continue")
def continue_writing(body: ContinueRequest):
    """AI 续写下一章"""
    story = story_mgr.get_story(body.story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    chapters = story.get("chapters", [])
    if not chapters:
        raise HTTPException(400, "没有已有章节，请先写第一章")
    last_ch = chapters[-1]
    result = agent.continue_chapter(story, last_ch.get("content", ""))
    return {"content": result}


@app.post("/api/agent/rewrite")
def rewrite_content(body: RewriteRequest):
    """AI 改写指定章节"""
    story = story_mgr.get_story(body.story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    target = None
    for ch in story.get("chapters", []):
        if ch["id"] == body.chapter_id:
            target = ch
            break
    if not target:
        raise HTTPException(404, "章节不存在")
    result = agent.rewrite_content(target.get("content", ""), body.instructions)
    return {"content": result}


@app.post("/api/agent/expand")
def expand_content(body: ExpandRequest):
    """AI 扩写指定章节"""
    story = story_mgr.get_story(body.story_id)
    if not story:
        raise HTTPException(404, "故事不存在")
    target = None
    for ch in story.get("chapters", []):
        if ch["id"] == body.chapter_id:
            target = ch
            break
    if not target:
        raise HTTPException(404, "章节不存在")
    result = agent.expand_content(target.get("content", ""))
    return {"content": result}


@app.post("/api/agent/chat")
def chat_with_agent(body: ChatRequest):
    """与 AI 顾问对话（网文趋势、题材推荐、创作建议）"""
    result = agent.chat(body.message)
    return {"content": result}


# ================================================================== #
#  静态文件服务（生产环境用）
# ================================================================== #
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# ================================================================== #
#  入口
# ================================================================== #
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
