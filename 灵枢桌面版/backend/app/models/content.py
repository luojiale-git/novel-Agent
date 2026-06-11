from pydantic import BaseModel, Field
from typing import Optional, List


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = ""
    project_id: str
    doc_type: str = "note"  # note, chapter, outline, research


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class Document(BaseModel):
    id: str
    title: str
    content: str
    project_id: str
    doc_type: str = "note"
    word_count: int = 0
    created_at: str = ""
    updated_at: str = ""
