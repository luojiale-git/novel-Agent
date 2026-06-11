from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..models.session import SessionCreate, Session, SessionList
from ..services.session_service import SessionService

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
service = SessionService()


@router.get("", response_model=SessionList)
def list_sessions(project_id: Optional[str] = Query(None)):
    sessions = service.list_sessions(project_id)
    return SessionList(sessions=sessions, total=len(sessions))


@router.post("", response_model=Session)
def create_session(data: SessionCreate):
    return service.create_session(data)


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str):
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(404, "会话不存在")
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str):
    if not service.delete_session(session_id):
        raise HTTPException(404, "会话不存在")
    return {"ok": True}


@router.put("/{session_id}/messages")
def save_messages(session_id: str, data: dict):
    messages = data.get("messages", [])
    service.save_session_messages(session_id, messages)
    return {"ok": True}
