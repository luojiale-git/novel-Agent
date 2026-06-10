"""持久化实现。

公开的统一接口：
    from infrastructure.persistence import (
        JsonStoryRepository,
        JsonCharacterRepository,
        JsonChapterRepository,
        JsonWorldBuildingRepository,
        JsonKnowledgeTripleRepository,
        JsonOutlineRepository,
        JsonUnitOfWork,
    )
"""

from infrastructure.persistence.json_repositories import (
    JsonChapterRepository,
    JsonCharacterRepository,
    JsonKnowledgeTripleRepository,
    JsonOutlineRepository,
    JsonStoryRepository,
    JsonUnitOfWork,
    JsonWorldBuildingRepository,
)

__all__ = [
    "JsonStoryRepository",
    "JsonCharacterRepository",
    "JsonChapterRepository",
    "JsonWorldBuildingRepository",
    "JsonKnowledgeTripleRepository",
    "JsonOutlineRepository",
    "JsonUnitOfWork",
]
