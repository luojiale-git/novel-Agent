from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProjectType(str, Enum):
    STORY = "story"  # 小说故事
    ARTICLE = "article"  # 文章写作
    RESEARCH = "research"  # 研究分析
    CODE = "code"  # 代码项目
    OTHER = "other"  # 其他


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    project_type: ProjectType = ProjectType.STORY


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None


class Project(BaseModel):
    id: str
    name: str
    description: str = ""
    project_type: ProjectType = ProjectType.STORY
    status: ProjectStatus = ProjectStatus.DRAFT
    created_at: str = ""
    updated_at: str = ""


class ProjectList(BaseModel):
    projects: List[Project]
    total: int
