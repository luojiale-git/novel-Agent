from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..models.content import DocumentCreate, DocumentUpdate, Document
from ..services.content_service import ContentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
service = ContentService()


@router.get("", response_model=list[Document])
def list_documents(project_id: Optional[str] = Query(None)):
    return service.list_documents(project_id)


@router.post("", response_model=Document)
def create_document(data: DocumentCreate):
    return service.create_document(data)


@router.get("/{doc_id}", response_model=Document)
def get_document(doc_id: str):
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


@router.put("/{doc_id}", response_model=Document)
def update_document(doc_id: str, data: DocumentUpdate):
    doc = service.update_document(doc_id, data)
    if not doc:
        raise HTTPException(404, "文档不存在")
    return doc


@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    if not service.delete_document(doc_id):
        raise HTTPException(404, "文档不存在")
    return {"ok": True}
