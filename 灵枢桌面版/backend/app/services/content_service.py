import json
import os
import uuid
from datetime import datetime
from typing import Optional
from ..models.content import Document, DocumentCreate, DocumentUpdate

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)


class ContentService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._index_file = os.path.join(DATA_DIR, "documents_index.json")

    def _load_index(self) -> dict:
        if os.path.exists(self._index_file):
            with open(self._index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"documents": []}

    def _save_index(self, data: dict):
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_documents(self, project_id: Optional[str] = None) -> list[Document]:
        index = self._load_index()
        docs = []
        for d in index.get("documents", []):
            if project_id and d.get("project_id") != project_id:
                continue
            docs.append(Document(**d))
        return sorted(docs, key=lambda x: x.updated_at, reverse=True)

    def create_document(
        self, data: DocumentCreate, doc_id: Optional[str] = None
    ) -> Document:
        now = datetime.now().isoformat()
        document = Document(
            id=doc_id or str(uuid.uuid4())[:8],
            title=data.title,
            content=data.content,
            project_id=data.project_id,
            doc_type=data.doc_type,
            word_count=len(data.content),
            created_at=now,
            updated_at=now,
        )
        index = self._load_index()
        index["documents"].append(document.model_dump())
        self._save_index(index)
        return document

    def get_document(self, doc_id: str) -> Optional[Document]:
        index = self._load_index()
        for d in index.get("documents", []):
            if d["id"] == doc_id:
                return Document(**d)
        return None

    def update_document(self, doc_id: str, data: DocumentUpdate) -> Optional[Document]:
        index = self._load_index()
        for i, d in enumerate(index["documents"]):
            if d["id"] == doc_id:
                if data.title is not None:
                    d["title"] = data.title
                if data.content is not None:
                    d["content"] = data.content
                    d["word_count"] = len(data.content)
                d["updated_at"] = datetime.now().isoformat()
                index["documents"][i] = d
                self._save_index(index)
                return Document(**d)
        return None

    def delete_document(self, doc_id: str) -> bool:
        index = self._load_index()
        for i, d in enumerate(index["documents"]):
            if d["id"] == doc_id:
                index["documents"].pop(i)
                self._save_index(index)
                return True
        return False
