from fastapi import APIRouter, HTTPException
from ..models.project import ProjectCreate, ProjectUpdate, Project, ProjectList
from ..services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
service = ProjectService()


@router.get("", response_model=ProjectList)
def list_projects():
    projects = service.list_projects()
    return ProjectList(projects=projects, total=len(projects))


@router.post("", response_model=Project)
def create_project(data: ProjectCreate):
    return service.create_project(data)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str):
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, data: ProjectUpdate):
    project = service.update_project(project_id, data)
    if not project:
        raise HTTPException(404, "项目不存在")
    return project


@router.delete("/{project_id}")
def delete_project(project_id: str):
    if not service.delete_project(project_id):
        raise HTTPException(404, "项目不存在")
    return {"ok": True}
