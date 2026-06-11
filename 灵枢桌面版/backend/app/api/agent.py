import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agent import Agent
from ..services.session_service import SessionService

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
session_service = SessionService()

_agent: Optional[Agent] = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/chat")
def chat(request: ChatRequest):
    """与 Agent 对话（流式 SSE 响应）"""
    agent = get_agent()

    # 如果指定了 session_id，恢复历史记忆
    if request.session_id:
        session = session_service.get_session(request.session_id)
        if session and hasattr(session, "messages") and session.messages:
            state = {"messages": [], "system_prompt": ""}
            for msg in session.messages:
                state["messages"].append({"role": msg.role, "content": msg.content})
            agent.load_memory_state(state)

    return StreamingResponse(
        _stream_chat(agent, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_chat(agent: Agent, request: ChatRequest):
    """生成 SSE 事件流"""
    full_response = ""
    try:
        for event_type, content in agent.run_stream(request.message):
            data = json.dumps(
                {"type": event_type, "content": content}, ensure_ascii=False
            )
            yield f"data: {data}\n\n"
            if event_type == "response":
                full_response += content
    finally:
        # 保存会话历史
        if request.session_id:
            state = agent.get_memory_state()
            message_list = state.get("messages", [])
            if message_list:
                session_service.save_session_messages(request.session_id, message_list)


@router.post("/reset")
def reset_agent():
    """重置 Agent 记忆"""
    agent = get_agent()
    agent.reset()
    return {"ok": True}


@router.get("/memory")
def get_memory():
    """获取当前 Agent 记忆状态"""
    agent = get_agent()
    return agent.get_memory_state()
