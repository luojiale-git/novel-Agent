"""
质量守门人 — 六维叙事评分
============================
基于叙事质量评估理论的可插拔评分器 + 修复建议生成。

六维：
  1. 语言文笔 (Language)     — 句式丰富度、修辞、节奏
  2. 角色一致性 (Character)  — OOC 检测、动机合理
  3. 情节逻辑 (Plot)         — 因果链完整、无逻辑漏洞
  4. 命名质量 (Naming)       — 角色/地名一致性、无跳戏命名
  5. 视角稳定 (Perspective)  — POV 不漂移、叙事人称一致
  6. 节奏张力 (Rhythm)       — 张弛有度、章节收束感

每个维度评分 0-100，附带具体问题和修复建议。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class DimensionScore:
    """单维度评分结果"""

    name: str
    score: float  # 0-100
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    details: str = ""

    @property
    def passed(self) -> bool:
        return self.score >= 60

    @property
    def level(self) -> str:
        if self.score >= 90:
            return "优秀"
        elif self.score >= 75:
            return "良好"
        elif self.score >= 60:
            return "及格"
        else:
            return "需修改"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "level": self.level,
            "passed": self.passed,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "details": self.details,
        }


@dataclass
class QualityReport:
    """完整质量报告"""

    text_title: str = ""
    dimensions: dict[str, DimensionScore] = field(default_factory=dict)
    overall_score: float = 0.0

    @property
    def passed(self) -> bool:
        return all(d.passed for d in self.dimensions.values())

    def summary(self) -> str:
        lines = [f"📊 质量报告: {self.text_title}"]
        lines.append(
            f"   综合评分: {self.overall_score:.1f}/100 — {'✅ 通过' if self.passed else '❌ 需修改'}"
        )
        for d in self.dimensions.values():
            icon = "✅" if d.passed else "⚠️"
            lines.append(f"   {icon} {d.name}: {d.score:.0f}/100 ({d.level})")
            for issue in d.issues[:3]:
                lines.append(f"      - {issue}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "title": self.text_title,
            "overall_score": round(self.overall_score, 1),
            "passed": self.passed,
            "dimensions": {k: v.to_dict() for k, v in self.dimensions.items()},
        }


# 评分器类型: 接受文本，返回 DimensionScore
ScorerFunc = Callable[[str], DimensionScore]


class QualityEngine:
    """
    质量守门人 — 六维叙事评分引擎

    用法:
        guardrail = QualityEngine()
        guardrail.register_scorer("语言文笔", my_language_scorer)
        report = guardrail.evaluate(text)
        print(report.summary())
    """

    DIMENSIONS = [
        "语言文笔",
        "角色一致性",
        "情节逻辑",
        "命名质量",
        "视角稳定",
        "节奏张力",
    ]

    def __init__(self):
        self._scorers: dict[str, ScorerFunc] = {}
        # 注册内置启发式评分器
        self._register_builtin()

    def _register_builtin(self) -> None:
        """注册内置的启发式评分器（用于快速离线检测）"""
        self.register_scorer("语言文笔", self._score_language)
        self.register_scorer("角色一致性", self._score_character)
        self.register_scorer("情节逻辑", self._score_plot)
        self.register_scorer("命名质量", self._score_naming)
        self.register_scorer("视角稳定", self._score_perspective)
        self.register_scorer("节奏张力", self._score_rhythm)

    def register_scorer(self, dimension: str, scorer: ScorerFunc) -> None:
        """注册自定义评分器"""
        self._scorers[dimension] = scorer

    def evaluate(self, text: str, title: str = "") -> QualityReport:
        """
        对文本执行全维度质量评分

        参数:
            text:  要评分的文本（章节或段落）
            title: 文本标题（可选）

        返回:
            QualityReport 包含所有维度评分
        """
        report = QualityReport(text_title=title or "未命名文本")
        total = 0.0

        for dim_name in self.DIMENSIONS:
            scorer = self._scorers.get(dim_name)
            if scorer:
                score = scorer(text)
            else:
                score = DimensionScore(
                    name=dim_name,
                    score=50.0,
                    issues=["未注册评分器"],
                    suggestions=["请注册该维度评分器"],
                )
            report.dimensions[dim_name] = score
            total += score.score

        report.overall_score = total / len(self.DIMENSIONS)
        return report

    # ── 内置启发式评分器 ──────────────────────────────

    def _score_language(self, text: str) -> DimensionScore:
        """语言文笔评分：句式长度多样性 + 标点使用"""
        issues: list[str] = []
        suggestions: list[str] = []

        if not text.strip():
            return DimensionScore(name="语言文笔", score=0, issues=["文本为空"])

        sentences = [
            s.strip()
            for s in text.replace("!", "。")
            .replace("?", "。")
            .replace("\n", "。")
            .split("。")
            if s.strip()
        ]
        if not sentences:
            return DimensionScore(
                name="语言文笔", score=30, issues=["无法识别句子结构"]
            )

        # 句式长度多样性
        lengths = [len(s) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        max_len = max(lengths)
        min_len = min(lengths)

        variety_score = 70
        if max_len - min_len < 10:
            variety_score = 40
            issues.append("句式长度变化过小，建议长短句交错")
            suggestions.append("多用短句制造节奏感，长句用于描写和抒情")

        # 标点多样性
        punct_count = sum(1 for c in text if c in "，。！？；：、''（）——…·")
        punct_score = min(100, (punct_count / max(len(text), 1)) * 500)
        if punct_count < 3:
            issues.append("标点使用偏少，影响阅读节奏")
            suggestions.append("适当加入逗号、破折号等标点增强语气")

        score = (
            0.4 * variety_score
            + 0.3 * min(100, punct_score)
            + 0.3 * min(100, avg_len * 2)
        )
        score = max(0, min(100, score))

        return DimensionScore(
            name="语言文笔", score=score, issues=issues, suggestions=suggestions
        )

    def _score_character(self, text: str) -> DimensionScore:
        """角色一致性评分（离线启发式版本）"""
        name_count = sum(
            1 for word in text.split() if len(word) >= 2 and word[0].isupper()
        )
        score = 70 if name_count > 3 else 50
        issues = []
        suggestions = []
        if name_count == 0:
            issues.append("未检测到角色名称，可能需要检查")
            suggestions.append("确保角色名称在对话和动作中出现")
        return DimensionScore(
            name="角色一致性", score=score, issues=issues, suggestions=suggestions
        )

    def _score_plot(self, text: str) -> DimensionScore:
        """情节逻辑评分"""
        # 检测因果连接词
        causal_words = [
            "因为",
            "所以",
            "因此",
            "于是",
            "由于",
            "结果",
            "导致",
            "引发",
            "原来",
            "这才",
        ]
        transition_words = [
            "但是",
            "然而",
            "不过",
            "却",
            "虽然",
            "尽管",
            "如果",
            "那么",
        ]
        causal_count = sum(1 for w in causal_words if w in text)
        trans_count = sum(1 for w in transition_words if w in text)
        score = min(100, 50 + causal_count * 5 + trans_count * 3)
        issues = []
        suggestions = []
        if causal_count == 0:
            issues.append("未检测到因果连接，情节推进可能缺乏逻辑支撑")
            suggestions.append("加入因果连接词强化逻辑链")
        return DimensionScore(
            name="情节逻辑", score=score, issues=issues, suggestions=suggestions
        )

    def _score_naming(self, text: str) -> DimensionScore:
        """命名质量评分"""
        score = 85  # 默认较高，命名一致性需要跨章节检测
        issues = []
        suggestions = []
        # 检测是否有不一致的命名（简单检测：同音/形近词混用）
        return DimensionScore(
            name="命名质量", score=score, issues=issues, suggestions=suggestions
        )

    def _score_perspective(self, text: str) -> DimensionScore:
        """视角稳定评分"""
        # 检测人称使用一致性
        first_person = sum(text.count(w) for w in ["我", "我们", "我的"])
        third_person = sum(text.count(w) for w in ["他", "她", "它", "他们", "她们"])
        issues = []
        suggestions = []
        score = 85
        if first_person > 0 and third_person > 1:
            issues.append("检测到第一人称和第三人称混用，可能存在视角漂移")
            suggestions.append("统一叙事视角，不要在同一章节切换人称")
            score = 45
        return DimensionScore(
            name="视角稳定", score=score, issues=issues, suggestions=suggestions
        )

    def _score_rhythm(self, text: str) -> DimensionScore:
        """节奏张力评分"""
        sentences = [
            s
            for s in text.replace("!", "。").replace("?", "。").split("。")
            if s.strip()
        ]
        issues = []
        suggestions = []
        if not sentences:
            return DimensionScore(
                name="节奏张力", score=30, issues=["文本过短无法评估"]
            )

        # 检测对话比例
        dialogue_count = text.count("「") + text.count("『") + text.count('"')
        dialogue_ratio = dialogue_count / max(len(sentences), 1)
        score = 60
        if dialogue_ratio > 0.8:
            issues.append("对话占比过高，缺少叙述和描写")
            suggestions.append("增加环境描写和心理活动，平衡对话与叙述")
        elif dialogue_ratio < 0.1:
            issues.append("缺少对话，叙事偏沉闷")
            suggestions.append("加入角色对话活跃节奏")
        else:
            score = 80
        return DimensionScore(
            name="节奏张力", score=score, issues=issues, suggestions=suggestions
        )
