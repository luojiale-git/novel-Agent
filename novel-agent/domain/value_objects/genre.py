"""
题材值对象 - 网文题材分类与特征
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Genre:
    """
    网文题材值对象
    支持预定义题材和自定义题材
    """

    name: str
    is_custom: bool = False
    subgenres: tuple = ()

    # 预定义题材
    PREDEFINED = {
        "玄幻",
        "仙侠",
        "修真",
        "奇幻",
        "都市",
        "言情",
        "历史",
        "军事",
        "游戏",
        "科幻",
        "悬疑",
        "恐怖",
        "武侠",
        "轻小说",
        "现实",
        "短篇",
    }

    # 热门子题材映射
    SUBGENRES = {
        "玄幻": ("诸天流", "重生流", "系统流", "无敌流", "神豪流", "废材流"),
        "仙侠": ("凡人流", "修真文明", "仙侠世界", "神话修真"),
        "都市": ("都市异能", "重生商战", "职场文", "电竞文", "豪门赘婿"),
        "言情": ("古代言情", "现代言情", "幻想言情", "青春文学"),
        "科幻": ("星际文明", "末世危机", "未来世界", "超级科技"),
        "悬疑": ("侦探推理", "灵异惊悚", "探险生存", "末日求生"),
    }

    def __post_init__(self):
        if not self.is_custom and self.name not in self.PREDEFINED:
            object.__setattr__(self, "is_custom", True)

    @classmethod
    def of(cls, name: str) -> "Genre":
        return cls(name=name, is_custom=name not in cls.PREDEFINED)

    @classmethod
    def all_predefined(cls) -> list[str]:
        return sorted(cls.PREDEFINED)

    def subgenre_list(self) -> tuple:
        return self.SUBGENRES.get(self.name, ())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "is_custom": self.is_custom,
            "subgenres": list(self.subgenres or self.subgenre_list()),
        }
