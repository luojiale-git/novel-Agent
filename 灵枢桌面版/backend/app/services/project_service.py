import json
import os
import uuid
from datetime import datetime
from typing import Optional
from ..models.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectType,
    ProjectStatus,
)

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)


class ProjectService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._index_file = os.path.join(DATA_DIR, "projects_index.json")

    def _load_index(self) -> dict:
        if os.path.exists(self._index_file):
            with open(self._index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"projects": []}

    def _save_index(self, data: dict):
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_project_file(self, project_id: str) -> str:
        return os.path.join(DATA_DIR, f"project_{project_id}.json")

    def list_projects(self) -> list[Project]:
        index = self._load_index()
        return [Project(**p) for p in index.get("projects", [])]

    def create_project(self, data: ProjectCreate) -> Project:
        now = datetime.now().isoformat()
        project = Project(
            id=str(uuid.uuid4())[:8],
            name=data.name,
            description=data.description,
            project_type=data.project_type,
            status=ProjectStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )
        index = self._load_index()
        index["projects"].append(project.model_dump())
        self._save_index(index)
        with open(self._get_project_file(project.id), "w", encoding="utf-8") as f:
            json.dump(project.model_dump(), f, ensure_ascii=False, indent=2)
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        index = self._load_index()
        for p in index.get("projects", []):
            if p["id"] == project_id:
                return Project(**p)
        return None

    def update_project(self, project_id: str, data: ProjectUpdate) -> Optional[Project]:
        index = self._load_index()
        for i, p in enumerate(index["projects"]):
            if p["id"] == project_id:
                if data.name is not None:
                    p["name"] = data.name
                if data.description is not None:
                    p["description"] = data.description
                if data.status is not None:
                    p["status"] = data.status.value
                p["updated_at"] = datetime.now().isoformat()
                index["projects"][i] = p
                self._save_index(index)
                with open(
                    self._get_project_file(project_id), "w", encoding="utf-8"
                ) as f:
                    json.dump(p, f, ensure_ascii=False, indent=2)
                return Project(**p)
        return None

    def delete_project(self, project_id: str) -> bool:
        index = self._load_index()
        for i, p in enumerate(index["projects"]):
            if p["id"] == project_id:
                index["projects"].pop(i)
                self._save_index(index)
                pf = self._get_project_file(project_id)
                if os.path.exists(pf):
                    os.remove(pf)
                return True
        return False
