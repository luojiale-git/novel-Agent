"""
Base service mixin — 常用 CRUD 辅助方法，消除服务层重复
"""

from typing import Optional


class _BaseService:
    """Mixin: 为应用服务提供 get/update/list/ID生成等公共辅助方法。

    子类只需提供 ``self.repo``（支持 get/save/delete + 可选 list_by_story）。
    """

    # ── 工具方法 ──────────────────────────────────────────────────────────

    @staticmethod
    def _generate_id(prefix: str) -> str:
        import uuid

        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    # ── 通用 CRUD 辅助 ───────────────────────────────────────────────────

    def _get(self, entity_id: str) -> Optional[dict]:
        """通用查询：repo.get → to_dict / None"""
        entity = self.repo.get(entity_id)
        return entity.to_dict() if entity else None

    def _update(self, entity_id: str, allowed_fields: set, **kwargs) -> Optional[dict]:
        """通用更新：get → 校验 → setattr → save → to_dict"""
        entity = self.repo.get(entity_id)
        if not entity:
            return None
        for k, v in kwargs.items():
            if k in allowed_fields and v is not None:
                setattr(entity, k, v)
        entity.updated_at = self._now()
        saved = self.repo.save(entity)
        return saved.to_dict()

    def _list_as_dicts(self, entities: list) -> list[dict]:
        """通用列表序列化"""
        return [e.to_dict() for e in entities]
