"""
知识图谱应用服务
"""

import logging
from typing import Optional

from ...domain.models.knowledge_triple import KnowledgeTriple
from ...domain.repositories.interfaces import KnowledgeTripleRepository
from ._base_service import _BaseService

logger = logging.getLogger(__name__)


class KnowledgeService(_BaseService):
    """知识图谱应用服务"""

    def __init__(self, repo: KnowledgeTripleRepository):
        self.repo = repo

    def add_triple(
        self,
        story_id: str,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        source: str = "",
        context: str = "",
    ) -> dict:
        """添加三元组"""
        triple = KnowledgeTriple(
            id=self._generate_id("KT"),
            story_id=story_id,
            subject=subject,
            predicate=predicate,
            object=object,
            confidence=confidence,
            source=source,
            context=context,
            created_at=self._now(),
        )
        return self.repo.save(triple).to_dict()

    def list_by_story(self, story_id: str) -> list[dict]:
        return self._list_as_dicts(self.repo.list_by_story(story_id))

    def search(self, story_id: str, query: str) -> list[dict]:
        triples = self.repo.search(story_id, query)
        return [t.to_dict() for t in triples]

    def extract_from_text(
        self, story_id: str, text: str, source: str = ""
    ) -> list[dict]:
        """从文本中提取三元组"""
        triples = KnowledgeTriple.from_text(text, story_id)
        results = []
        for t in triples:
            t.source = source
            t.context = text[:200]
            saved = self.repo.save(t)
            results.append(saved.to_dict())
        return results

    def delete_by_story(self, story_id: str):
        self.repo.delete_by_story(story_id)
