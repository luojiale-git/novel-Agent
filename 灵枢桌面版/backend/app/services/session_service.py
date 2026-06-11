import json
import os
import uuid
from datetime import datetime
from typing import Optional
from ..models.session import Session, SessionCreate, Message

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)


class SessionService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._index_file = os.path.join(DATA_DIR, "sessions_index.json")

    def _load_index(self) -> dict:
        if os.path.exists(self._index_file):
            with open(self._index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"sessions": []}

    def _save_index(self, data: dict):
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_session_file(self, session_id: str) -> str:
        return os.path.join(DATA_DIR, f"session_{session_id}.json")

    def list_sessions(self, project_id: Optional[str] = None) -> list[Session]:
        index = self._load_index()
        sessions = []
        for s in index.get("sessions", []):
            if project_id and s.get("project_id") != project_id:
                continue
            sessions.append(Session(**s))
        return sorted(sessions, key=lambda x: x.updated_at, reverse=True)

    def create_session(self, data: SessionCreate) -> Session:
        now = datetime.now().isoformat()
        session = Session(
            id=str(uuid.uuid4())[:8],
            name=data.name,
            project_id=data.project_id,
            created_at=now,
            updated_at=now,
        )
        index = self._load_index()
        index["sessions"].append(session.model_dump())
        self._save_index(index)
        with open(self._get_session_file(session.id), "w", encoding="utf-8") as f:
            json.dump(session.model_dump(), f, ensure_ascii=False, indent=2)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        sf = self._get_session_file(session_id)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session(**data)
        return None

    def save_session_messages(self, session_id: str, messages: list[dict]) -> bool:
        sf = self._get_session_file(session_id)
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data["messages"] = messages
        data["updated_at"] = datetime.now().isoformat()
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        index = self._load_index()
        for s in index["sessions"]:
            if s["id"] == session_id:
                s["updated_at"] = data["updated_at"]
                s["message_count"] = len(messages)
                break
        self._save_index(index)
        return True

    def delete_session(self, session_id: str) -> bool:
        index = self._load_index()
        for i, s in enumerate(index["sessions"]):
            if s["id"] == session_id:
                index["sessions"].pop(i)
                self._save_index(index)
                sf = self._get_session_file(session_id)
                if os.path.exists(sf):
                    os.remove(sf)
                return True
        return False
