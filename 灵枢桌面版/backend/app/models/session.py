from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Message(BaseModel):
    role: str  # user, assistant, system, tool
    content: str
    timestamp: str = ""


class SessionCreate(BaseModel):
    name: str = Field(default="新对话", max_length=200)
    project_id: Optional[str] = None


class Session(BaseModel):
    id: str
    name: str
    project_id: Optional[str] = None
    messages: List[Message] = []
    created_at: str = ""
    updated_at: str = ""


class SessionList(BaseModel):
    sessions: List[Session]
    total: int
