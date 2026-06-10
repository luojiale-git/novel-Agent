"""
StoryCraft 模块单元测试
=======================
覆盖 bible / memory / quality / state_machine / prompts 各模块。
"""

from __future__ import annotations

import json
import os
import tempfile
import time

import pytest

from storycraft.bible import (
    CharacterProfile,
    CharacterTrait,
    Location,
    StoryBible,
)
from storycraft.memory import MemoryEntry, NarrativeMemory
from storycraft.quality import (
    DimensionScore,
    QualityEngine,
    QualityReport,
)
from storycraft.state_machine import (
    ChapterRecord,
    NarrativePhase,
    NarrativeStateMachine,
    PlotHook,
)
from storycraft.prompts import PromptTemplate, PromptWorkshop


# ═══════════════════════════════════════════════════════════
# Bible 模块测试
# ═══════════════════════════════════════════════════════════


class TestCharacterTrait:
    def test_init(self):
        t = CharacterTrait(
            name="勇敢", category="personality", description="不畏危险", intensity=0.9
        )
        assert t.name == "勇敢"
        assert t.category == "personality"
        assert t.intensity == 0.9

    def test_to_dict(self):
        t = CharacterTrait(name="冷静", intensity=0.8)
        d = t.to_dict()
        assert d["name"] == "冷静"
        assert d["category"] == "personality"
        assert d["intensity"] == 0.8


class TestCharacterProfile:
    def test_defaults(self):
        c = CharacterProfile(id="c1", name="林夜")
        assert c.role == ""
        assert c.revision == 0
        assert c.current_state == {}
        assert c.traits == []

    def test_update_state(self):
        c = CharacterProfile(id="c1", name="林夜")
        c.update_state(mood="愤怒", goal="寻找真相")
        assert c.current_state["mood"] == "愤怒"
        assert c.current_state["goal"] == "寻找真相"
        assert c.revision == 1

    def test_update_state_multiple_times(self):
        c = CharacterProfile(id="c1", name="林夜")
        c.update_state(mood="平静")
        assert c.revision == 1
        c.update_state(mood="愤怒")
        assert c.revision == 2
        assert c.current_state["mood"] == "愤怒"

    def test_get_mask_summary_with_state(self):
        c = CharacterProfile(id="c1", name="林夜")
        c.update_state(mood="愤怒", goal="决战")
        summary = c.get_mask_summary()
        assert "林夜" in summary
        assert "第1版面具" in summary
        assert "mood=愤怒" in summary

    def test_get_mask_summary_empty(self):
        c = CharacterProfile(id="c1", name="林夜")
        summary = c.get_mask_summary()
        assert "状态无变化" in summary

    def test_consistency_check_name_mentioned(self):
        c = CharacterProfile(id="c1", name="林夜")
        issues = c.consistency_check("林夜拔出了剑")
        assert issues == []

    def test_consistency_check_name_not_mentioned(self):
        c = CharacterProfile(id="c1", name="林夜")
        issues = c.consistency_check("四周一片寂静")
        assert len(issues) == 1
        assert "林夜" in issues[0]

    def test_to_dict(self):
        c = CharacterProfile(id="c1", name="林夜", role="主角")
        c.traits.append(CharacterTrait(name="勇敢"))
        d = c.to_dict()
        assert d["id"] == "c1"
        assert d["name"] == "林夜"
        assert d["role"] == "主角"
        assert len(d["traits"]) == 1


class TestLocation:
    def test_init(self):
        loc = Location(id="loc1", name="幽都", type="world", description="暗黑之城")
        assert loc.id == "loc1"
        assert loc.name == "幽都"
        assert loc.type == "world"

    def test_to_dict(self):
        loc = Location(id="loc1", name="幽都", connections=["loc2", "loc3"])
        d = loc.to_dict()
        assert d["name"] == "幽都"
        assert d["connections"] == ["loc2", "loc3"]


class TestStoryBible:
    def test_init(self):
        bible = StoryBible("test_story", "测试故事")
        assert bible.story_id == "test_story"
        assert bible.title == "测试故事"
        assert bible.characters == {}
        assert bible.locations == {}

    def test_add_character(self):
        bible = StoryBible("test")
        c = CharacterProfile(id="c1", name="林夜")
        bible.add_character(c)
        assert "c1" in bible.characters

    def test_get_character_exists(self):
        bible = StoryBible("test")
        bible.add_character(CharacterProfile(id="c1", name="林夜"))
        c = bible.get_character("c1")
        assert c is not None
        assert c.name == "林夜"

    def test_get_character_not_exists(self):
        bible = StoryBible("test")
        assert bible.get_character("nonexistent") is None

    def test_remove_character_exists(self):
        bible = StoryBible("test")
        bible.add_character(CharacterProfile(id="c1", name="林夜"))
        assert bible.remove_character("c1") is True
        assert "c1" not in bible.characters

    def test_remove_character_not_exists(self):
        bible = StoryBible("test")
        assert bible.remove_character("nonexistent") is False

    def test_list_characters_all(self):
        bible = StoryBible("test")
        bible.add_character(CharacterProfile(id="c1", name="林夜", role="主角"))
        bible.add_character(CharacterProfile(id="c2", name="黑影", role="反派"))
        bible.add_character(CharacterProfile(id="c3", name="阿九", role="配角"))
        chars = bible.list_characters()
        assert len(chars) == 3

    def test_list_characters_by_role(self):
        bible = StoryBible("test")
        bible.add_character(CharacterProfile(id="c1", name="林夜", role="主角"))
        bible.add_character(CharacterProfile(id="c2", name="黑影", role="反派"))
        chars = bible.list_characters(role="主角")
        assert len(chars) == 1
        assert chars[0].name == "林夜"

    def test_add_location(self):
        bible = StoryBible("test")
        loc = Location(id="loc1", name="幽都")
        bible.add_location(loc)
        assert "loc1" in bible.locations

    def test_get_location(self):
        bible = StoryBible("test")
        bible.add_location(Location(id="loc1", name="幽都"))
        loc = bible.get_location("loc1")
        assert loc is not None
        assert loc.name == "幽都"

    def test_remove_location(self):
        bible = StoryBible("test")
        bible.add_location(Location(id="loc1", name="幽都"))
        assert bible.remove_location("loc1") is True
        assert "loc1" not in bible.locations

    def test_check_all_masks(self):
        bible = StoryBible("test")
        bible.add_character(CharacterProfile(id="c1", name="林夜"))
        bible.add_character(CharacterProfile(id="c2", name="黑影"))
        issues = bible.check_all_masks("黑影在黑暗中现身")
        assert len(issues) == 1  # 林夜未出场
        assert "林夜" in issues[0]

    def test_to_dict(self):
        bible = StoryBible("sid", "故事")
        bible.add_character(CharacterProfile(id="c1", name="林夜"))
        bible.add_location(Location(id="loc1", name="幽都"))
        bible.settings["magic"] = "禁术"
        d = bible.to_dict()
        assert d["story_id"] == "sid"
        assert len(d["characters"]) == 1
        assert len(d["locations"]) == 1
        assert d["settings"]["magic"] == "禁术"

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bible.json")
            bible = StoryBible("sid", "故事", data_dir=tmpdir)
            bible.add_character(CharacterProfile(id="c1", name="林夜", role="主角"))
            bible.save(path)
            assert os.path.exists(path)

            loaded = StoryBible.load(path)
            assert loaded.story_id == "sid"
            assert loaded.title == "故事"
            c = loaded.get_character("c1")
            assert c is not None
            assert c.name == "林夜"
            assert c.role == "主角"

    def test_save_without_path_no_data_dir(self):
        """无 data_dir 且不传 path 时 save 不应抛异常"""
        bible = StoryBible("sid")
        bible.save()  # should not raise

    def test_load_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            StoryBible.load("/nonexistent/bible.json")


# ═══════════════════════════════════════════════════════════
# Memory 模块测试
# ═══════════════════════════════════════════════════════════


class TestMemoryEntry:
    def test_defaults(self):
        e = MemoryEntry()
        assert e.memory_type == "plot"
        assert e.importance == 5
        assert e.id == 0

    def test_to_dict(self):
        e = MemoryEntry(id=1, content="测试", memory_type="detail", importance=8)
        d = e.to_dict()
        assert d["id"] == 1
        assert d["content"] == "测试"
        assert d["memory_type"] == "detail"
        assert "created_at" in d


class TestNarrativeMemory:
    def test_init_memory(self):
        mem = NarrativeMemory(":memory:")
        assert mem.db_path == ":memory:"
        mem.conn  # 触发初始化
        assert mem._conn is not None

    def test_store_and_count(self):
        mem = NarrativeMemory(":memory:")
        mem.store(
            "plot", "林夜发现了古剑", keywords="古剑,林夜", chapter=1, importance=8
        )
        assert mem.count() == 1

    def test_store_returns_id(self):
        mem = NarrativeMemory(":memory:")
        mid = mem.store("plot", "测试事件")
        assert isinstance(mid, int)
        assert mid > 0

    def test_get_existing(self):
        mem = NarrativeMemory(":memory:")
        mid = mem.store("plot", "林夜发现了古剑")
        entry = mem.get(mid)
        assert entry is not None
        assert entry["content"] == "林夜发现了古剑"
        assert entry["id"] == mid

    def test_get_nonexistent(self):
        mem = NarrativeMemory(":memory:")
        assert mem.get(99999) is None

    def test_update(self):
        mem = NarrativeMemory(":memory:")
        mid = mem.store("plot", "原内容")
        assert mem.update(mid, content="新内容") is True
        entry = mem.get(mid)
        assert entry["content"] == "新内容"

    def test_update_no_fields(self):
        mem = NarrativeMemory(":memory:")
        mid = mem.store("plot", "内容")
        assert mem.update(mid) is False  # 无有效字段

    def test_delete(self):
        mem = NarrativeMemory(":memory:")
        mid = mem.store("plot", "待删除")
        mem.delete(mid)
        assert mem.get(mid) is None

    def test_search_by_keyword(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "林夜在幽都地下发现古剑", keywords="古剑,幽都", chapter=5)
        mem.store("detail", "古剑名为'灭世'", keywords="古剑,灭世", chapter=6)
        results = mem.search("古剑")
        assert len(results) >= 2

    def test_search_empty_query(self):
        """空查询应返回最近记忆"""
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "事件A")
        mem.store("plot", "事件B")
        results = mem.search("")
        assert len(results) == 2

    def test_search_with_type_filter(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "情节事件")
        mem.store("detail", "细节描述")
        results = mem.search("事件", memory_type="plot")
        assert all(r["memory_type"] == "plot" for r in results)

    def test_fts_fallback_on_syntax_error(self):
        """FTS 查询语法错误时降级到 LIKE 搜索"""
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "林夜的故事")
        # 使用特殊字符触发 FTS 错误
        results = mem.search("林夜 AND")
        assert len(results) >= 0  # 降级后不抛异常

    def test_list_recent(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "事件A", chapter=1)
        mem.store("plot", "事件B", chapter=2)
        mem.store("detail", "细节C", chapter=3)
        results = mem.list_recent(limit=2)
        assert len(results) <= 2

    def test_list_recent_with_type(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "事件A")
        mem.store("detail", "细节B")
        results = mem.list_recent(memory_type="detail")
        assert len(results) == 1
        assert results[0]["memory_type"] == "detail"

    def test_search_by_chapter(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "第5章事件", keywords="", chapter=5)
        mem.store("plot", "第6章事件", keywords="", chapter=6)
        results = mem.search_by_chapter(5)
        assert len(results) == 1
        assert results[0]["source_chapter"] == 5

    def test_recall_context(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "林夜进入幽都", keywords="林夜,幽都", chapter=1)
        mem.store("detail", "幽都入口有封印", keywords="幽都,封印", chapter=1)
        context = mem.recall_context("幽都", window=1)
        assert "林夜" in context or "幽都" in context

    def test_clear(self):
        mem = NarrativeMemory(":memory:")
        mem.store("plot", "事件A")
        mem.store("detail", "事件B")
        assert mem.count() == 2
        mem.clear()
        assert mem.count() == 0

    def test_context_manager(self):
        with NarrativeMemory(":memory:") as mem:
            mem.store("plot", "在上下文管理器中")
            assert mem.count() == 1
        # 退出后连接应关闭
        assert mem._conn is None

    def test_file_based_db(self):
        """基于文件的数据库测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            mem = NarrativeMemory(db_path)
            mem.store("plot", "文件存储测试", chapter=1)
            assert mem.count() == 1
            mem.close()

            # 重新打开，数据应持久化
            mem2 = NarrativeMemory(db_path)
            assert mem2.count() == 1
            mem2.close()


# ═══════════════════════════════════════════════════════════
# Quality 模块测试
# ═══════════════════════════════════════════════════════════


class TestDimensionScore:
    def test_passed_high(self):
        ds = DimensionScore(name="测试", score=80)
        assert ds.passed is True

    def test_passed_low(self):
        ds = DimensionScore(name="测试", score=40)
        assert ds.passed is False

    def test_passed_boundary(self):
        ds = DimensionScore(name="测试", score=60)
        assert ds.passed is True

    def test_level_excellent(self):
        assert DimensionScore(name="", score=95).level == "优秀"

    def test_level_good(self):
        assert DimensionScore(name="", score=80).level == "良好"

    def test_level_pass(self):
        assert DimensionScore(name="", score=65).level == "及格"

    def test_level_fail(self):
        assert DimensionScore(name="", score=30).level == "需修改"

    def test_level_boundaries(self):
        assert DimensionScore(name="", score=90).level == "优秀"
        assert DimensionScore(name="", score=75).level == "良好"
        assert DimensionScore(name="", score=60).level == "及格"
        assert DimensionScore(name="", score=0).level == "需修改"

    def test_to_dict(self):
        ds = DimensionScore(
            name="语言文笔", score=75, issues=["问题1"], suggestions=["建议1"]
        )
        d = ds.to_dict()
        assert d["name"] == "语言文笔"
        assert d["score"] == 75
        assert d["passed"] is True
        assert d["level"] == "良好"
        assert d["issues"] == ["问题1"]


class TestQualityReport:
    def test_all_passed(self):
        report = QualityReport(text_title="测试")
        report.dimensions["a"] = DimensionScore(name="a", score=80)
        report.dimensions["b"] = DimensionScore(name="b", score=90)
        report.overall_score = 85.0
        assert report.passed is True

    def test_some_failed(self):
        report = QualityReport(text_title="测试")
        report.dimensions["a"] = DimensionScore(name="a", score=80)
        report.dimensions["b"] = DimensionScore(name="b", score=30)
        assert report.passed is False

    def test_summary(self):
        report = QualityReport(text_title="第一章")
        report.dimensions["语言"] = DimensionScore(name="语言", score=85)
        report.overall_score = 85.0
        summary = report.summary()
        assert "第一章" in summary
        assert "85" in summary

    def test_summary_empty(self):
        report = QualityReport()
        summary = report.summary()
        assert "质量报告" in summary

    def test_to_dict(self):
        report = QualityReport(text_title="第一章")
        report.dimensions["语言"] = DimensionScore(name="语言", score=85)
        report.overall_score = 85.0
        d = report.to_dict()
        assert d["title"] == "第一章"
        assert d["overall_score"] == 85.0
        assert d["passed"] is True


class TestQualityEngine:
    def test_init(self):
        qg = QualityEngine()
        assert len(qg._scorers) == 6  # 六维内置评分器

    def test_register_custom_scorer(self):
        qg = QualityEngine()
        qg.register_scorer(
            "自定义维度", lambda t: DimensionScore(name="自定义", score=100)
        )
        assert "自定义维度" in qg._scorers

    @pytest.fixture
    def sample_text(self):
        return (
            "林夜站在幽都的城门前。他深吸一口气，握紧了手中的古剑。\n"
            "「来吧，」他低声说，「我等这一刻已经很久了。」\n"
            "城门缓缓打开，一股腐朽的气息扑面而来。"
        )

    def test_evaluate_return_report(self, sample_text):
        qg = QualityEngine()
        report = qg.evaluate(sample_text, title="第一章")
        assert isinstance(report, QualityReport)
        assert report.text_title == "第一章"
        assert len(report.dimensions) == 6

    def test_evaluate_overall_score_range(self, sample_text):
        qg = QualityEngine()
        report = qg.evaluate(sample_text)
        assert 0 <= report.overall_score <= 100

    def test_evaluate_all_six_dimensions(self, sample_text):
        qg = QualityEngine()
        report = qg.evaluate(sample_text)
        expected_dims = {
            "语言文笔",
            "角色一致性",
            "情节逻辑",
            "命名质量",
            "视角稳定",
            "节奏张力",
        }
        assert set(report.dimensions.keys()) == expected_dims

    def test_score_language_empty(self):
        qg = QualityEngine()
        ds = qg._score_language("")
        assert ds.score == 0
        assert "文本为空" in ds.issues

    def test_score_language_no_sentences(self):
        qg = QualityEngine()
        ds = qg._score_language("???")
        assert ds.score == 30  # 无法识别句子结构

    def test_score_language_normal(self):
        qg = QualityEngine()
        text = "林夜走进了幽都。四周一片漆黑。远处传来低语声。"
        ds = qg._score_language(text)
        assert 0 <= ds.score <= 100

    def test_score_character_with_names(self):
        qg = QualityEngine()
        text = "Alice Bob Charlie David 在对话"
        ds = qg._score_character(text)
        assert ds.score == 70

    def test_score_character_no_names(self):
        qg = QualityEngine()
        ds = qg._score_character("一片寂静，什么也没有")
        assert ds.score == 50

    def test_score_plot_with_causal_words(self):
        qg = QualityEngine()
        text = "因为下雨，所以路滑。因此他摔倒了。"
        ds = qg._score_plot(text)
        assert ds.score >= 50

    def test_score_plot_no_causal_words(self):
        qg = QualityEngine()
        ds = qg._score_plot("今天天气不错。")
        assert ds.score >= 50
        assert len(ds.issues) > 0

    def test_score_naming(self):
        qg = QualityEngine()
        ds = qg._score_naming("任何文本")
        assert ds.score == 85

    def test_score_perspective_mixed(self):
        qg = QualityEngine()
        text = "我看着他。他走了过来。我们四目相对。"  # 第一人称和第三人称混用
        ds = qg._score_perspective(text)
        assert ds.score == 45  # 视角漂移

    def test_score_perspective_consistent(self):
        qg = QualityEngine()
        text = "他看着她。她笑了笑。他点了点头。"
        ds = qg._score_perspective(text)
        assert ds.score == 85

    def test_score_rhythm_no_dialogue(self):
        qg = QualityEngine()
        text = "环境描写。静态叙述。缺少对话。"
        ds = qg._score_rhythm(text)
        assert ds.score == 60  # 缺少对话

    def test_score_rhythm_good_dialogue(self):
        qg = QualityEngine()
        text = "他说：「你好」。她回答：「你好吗」。环境描写。心理活动。叙述转场。"
        ds = qg._score_rhythm(text)
        assert ds.score in (60, 80)

    def test_evaluate_unregistered_dimension(self):
        """未注册评分器的维度应给默认 50 分"""
        qg = QualityEngine()
        # 模拟某个评分器未注册
        qg._scorers = {}
        report = qg.evaluate("测试文本")
        for ds in report.dimensions.values():
            assert ds.score == 50.0
            assert "未注册评分器" in ds.issues


# ═══════════════════════════════════════════════════════════
# State Machine 模块测试
# ═══════════════════════════════════════════════════════════


class TestNarrativePhase:
    def test_from_progress_opening(self):
        assert NarrativePhase.from_progress(0.0) == NarrativePhase.OPENING
        assert NarrativePhase.from_progress(0.24) == NarrativePhase.OPENING

    def test_from_progress_development(self):
        assert NarrativePhase.from_progress(0.25) == NarrativePhase.DEVELOPMENT
        assert NarrativePhase.from_progress(0.74) == NarrativePhase.DEVELOPMENT

    def test_from_progress_convergence(self):
        assert NarrativePhase.from_progress(0.75) == NarrativePhase.CONVERGENCE
        assert NarrativePhase.from_progress(0.89) == NarrativePhase.CONVERGENCE

    def test_from_progress_finale(self):
        assert NarrativePhase.from_progress(0.90) == NarrativePhase.FINALE
        assert NarrativePhase.from_progress(1.0) == NarrativePhase.FINALE

    def test_allows_new_hooks(self):
        assert NarrativePhase.OPENING.allows_new_hooks() is True
        assert NarrativePhase.DEVELOPMENT.allows_new_hooks() is True
        assert NarrativePhase.CONVERGENCE.allows_new_hooks() is False
        assert NarrativePhase.FINALE.allows_new_hooks() is False

    def test_allows_slice_of_life(self):
        assert NarrativePhase.OPENING.allows_slice_of_life() is True
        assert NarrativePhase.DEVELOPMENT.allows_slice_of_life() is True
        assert NarrativePhase.CONVERGENCE.allows_slice_of_life() is False
        assert NarrativePhase.FINALE.allows_slice_of_life() is False

    def test_requires_hook_resolution(self):
        assert NarrativePhase.OPENING.requires_hook_resolution() is False
        assert NarrativePhase.DEVELOPMENT.requires_hook_resolution() is False
        assert NarrativePhase.CONVERGENCE.requires_hook_resolution() is True
        assert NarrativePhase.FINALE.requires_hook_resolution() is True

    def test_tension_multiplier(self):
        assert NarrativePhase.OPENING.tension_multiplier() == 0.6
        assert NarrativePhase.DEVELOPMENT.tension_multiplier() == 1.0
        assert NarrativePhase.CONVERGENCE.tension_multiplier() == 1.5
        assert NarrativePhase.FINALE.tension_multiplier() == 2.0

    def test_label_cn(self):
        assert NarrativePhase.OPENING.label_cn() == "起·开局"
        assert NarrativePhase.FINALE.label_cn() == "合·终章"


class TestPlotHook:
    def test_defaults(self):
        h = PlotHook(id="h1", description="测试伏笔", chapter_planted=1)
        assert h.is_resolved is False
        assert h.category == "general"

    def test_to_dict(self):
        h = PlotHook(
            id="h1", description="古剑来历", chapter_planted=5, category="mystery"
        )
        d = h.to_dict()
        assert d["id"] == "h1"
        assert d["category"] == "mystery"
        assert d["is_resolved"] is False


class TestChapterRecord:
    def test_defaults(self):
        cr = ChapterRecord(number=1)
        assert cr.title == ""
        assert cr.word_count == 0

    def test_to_dict(self):
        cr = ChapterRecord(number=1, title="第一章", word_count=2000)
        d = cr.to_dict()
        assert d["number"] == 1
        assert d["title"] == "第一章"
        assert d["word_count"] == 2000


class TestNarrativeStateMachine:
    def test_init(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        assert nsm.story_id == "test"
        assert nsm.total_chapters == 80
        assert nsm.current_chapter == 0
        assert nsm.phase == NarrativePhase.OPENING

    def test_progress_zero(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        assert nsm.progress == 0.0

    def test_progress_full(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(80)
        assert nsm.progress == 1.0

    def test_progress_half(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(40)
        assert nsm.progress == 0.5

    def test_set_current_chapter_updates_phase(self):
        nsm = NarrativeStateMachine("test", total_chapters=100)
        nsm.set_current_chapter(10)
        assert nsm.phase == NarrativePhase.OPENING
        nsm.set_current_chapter(50)
        assert nsm.phase == NarrativePhase.DEVELOPMENT
        nsm.set_current_chapter(80)
        assert nsm.phase == NarrativePhase.CONVERGENCE
        nsm.set_current_chapter(95)
        assert nsm.phase == NarrativePhase.FINALE

    def test_set_current_chapter_does_not_exceed_total(self):
        nsm = NarrativeStateMachine("test", total_chapters=50)
        nsm.set_current_chapter(999)
        assert nsm.current_chapter == 50

    def test_advance(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.advance(5)
        assert nsm.current_chapter == 15

    def test_advance_default(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.advance()
        assert nsm.current_chapter == 11

    def test_plant_hook_opening(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)  # opening
        hook = nsm.plant_hook("h1", "神秘古剑", chapter=5)
        assert hook is not None
        assert "h1" in nsm.hooks

    def test_plant_hook_convergence_blocked(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(70)  # convergence (70/80 = 87.5%)
        hook = nsm.plant_hook("h2", "新伏笔", chapter=70)
        assert hook is None  # 被拒绝

    def test_plant_hook_finale_blocked(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(75)  # finale (75/80 = 93.75%)
        hook = nsm.plant_hook("h3", "终局伏笔", chapter=75)
        assert hook is None

    def test_resolve_hook(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.plant_hook("h1", "伏笔", chapter=5)
        result = nsm.resolve_hook("h1", chapter=30, note="回收了")
        assert result is True
        assert nsm.hooks["h1"].is_resolved is True
        assert nsm.hooks["h1"].chapter_resolved == 30

    def test_resolve_hook_nonexistent(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        result = nsm.resolve_hook("nonexistent", chapter=10)
        assert result is False

    def test_resolve_hook_twice(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.plant_hook("h1", "伏笔", chapter=5)
        nsm.resolve_hook("h1", chapter=30)
        result = nsm.resolve_hook("h1", chapter=40)  # 第二次回收
        assert result is False  # 已回收

    def test_pending_hooks(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.plant_hook("h1", "未回收", chapter=1)
        nsm.plant_hook("h2", "已回收", chapter=2)
        nsm.resolve_hook("h2", chapter=10)
        pending = nsm.pending_hooks()
        assert len(pending) == 1
        assert pending[0].id == "h1"

    def test_resolved_hooks(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.plant_hook("h1", "未回收", chapter=1)
        nsm.plant_hook("h2", "已回收", chapter=2)
        nsm.resolve_hook("h2", chapter=10)
        resolved = nsm.resolved_hooks()
        assert len(resolved) == 1
        assert resolved[0].id == "h2"

    def test_hook_resolution_rate_empty(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        assert nsm.hook_resolution_rate() == 1.0  # 无伏笔视为完全回收

    def test_hook_resolution_rate(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.set_current_chapter(10)
        nsm.plant_hook("h1", "伏笔1", chapter=1)
        nsm.plant_hook("h2", "伏笔2", chapter=2)
        nsm.resolve_hook("h1", chapter=10)
        assert nsm.hook_resolution_rate() == 0.5

    def test_record_chapter(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        rec = nsm.record_chapter(
            number=1, title="第一章", word_count=2000, tension=60.0
        )
        assert isinstance(rec, ChapterRecord)
        assert len(nsm.chapters) == 1
        assert nsm.tension_history == [60.0]

    def test_record_chapter_replace(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.record_chapter(number=1, title="初版", word_count=1000)
        nsm.record_chapter(number=1, title="修订版", word_count=2000)
        assert len(nsm.chapters) == 1
        assert nsm.chapters[0].title == "修订版"

    def test_audit_structure(self):
        nsm = NarrativeStateMachine("test", total_chapters=100)
        nsm.set_current_chapter(50)
        report = nsm.audit()
        assert report["story_id"] == "test"
        assert report["phase"] == "development"
        assert report["progress"] == 0.5
        assert "hook_stats" in report
        assert "tension" in report
        assert "warnings" in report
        assert report["healthy"] is True

    def test_audit_hook_warning(self):
        nsm = NarrativeStateMachine("test", total_chapters=100)
        nsm.set_current_chapter(80)  # convergence
        nsm.plant_hook("h1", "未回收伏笔", chapter=10)
        nsm.plant_hook("h2", "另一个未回收", chapter=20)
        report = nsm.audit()
        assert len(report["warnings"]) > 0

    def test_audit_tension_warning(self):
        nsm = NarrativeStateMachine("test", total_chapters=100)
        nsm.set_current_chapter(90)  # finale
        nsm.record_chapter(number=86, tension=10.0)
        nsm.record_chapter(number=87, tension=15.0)
        nsm.record_chapter(number=88, tension=20.0)
        nsm.record_chapter(number=89, tension=25.0)
        nsm.record_chapter(number=90, tension=30.0)
        report = nsm.audit()
        # 平均张力可能低于30
        if report["tension"]["average"] < 30:
            assert len(report["warnings"]) > 0

    def test_suggest_next_chapter_focus(self):
        nsm = NarrativeStateMachine("test", total_chapters=100)
        nsm.set_current_chapter(10)
        suggestion = nsm.suggest_next_chapter_focus()
        assert "开局阶段" in suggestion
        nsm.set_current_chapter(50)
        suggestion = nsm.suggest_next_chapter_focus()
        assert "展开阶段" in suggestion

    def test_to_dict(self):
        nsm = NarrativeStateMachine("test", total_chapters=80, title="测试小说")
        nsm.set_current_chapter(10)
        nsm.plant_hook("h1", "伏笔", chapter=5)
        nsm.record_chapter(number=1, title="第一章")
        d = nsm.to_dict()
        assert d["story_id"] == "test"
        assert d["title"] == "测试小说"
        assert d["current_chapter"] == 10
        assert len(d["hooks"]) == 1
        assert len(d["chapters"]) == 1

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "state.json")
            nsm = NarrativeStateMachine(
                "test", total_chapters=80, title="测试", data_dir=tmpdir
            )
            nsm.set_current_chapter(10)
            nsm.plant_hook("h1", "伏笔", chapter=5)
            nsm.save(path)
            assert os.path.exists(path)

            loaded = NarrativeStateMachine.load(path)
            assert loaded.story_id == "test"
            assert loaded.total_chapters == 80
            assert loaded.current_chapter == 10
            assert "h1" in loaded.hooks

    def test_save_without_path(self):
        nsm = NarrativeStateMachine("test", total_chapters=80)
        nsm.save()  # should not raise

    def test_progress_no_chapters(self):
        nsm = NarrativeStateMachine("test", total_chapters=0)
        assert nsm.progress == 0.0


# ═══════════════════════════════════════════════════════════
# Prompts 模块测试
# ═══════════════════════════════════════════════════════════


class TestPromptTemplate:
    def test_render_all_vars_provided(self):
        tmpl = PromptTemplate(
            name="test",
            template="角色：{name}，场景：{scene}",
            variables=["name", "scene"],
        )
        result = tmpl.render(name="林夜", scene="雨夜")
        assert result == "角色：林夜，场景：雨夜"

    def test_render_missing_var_placeholder(self):
        tmpl = PromptTemplate(
            name="test",
            template="角色：{name}，场景：{scene}",
            variables=["name", "scene"],
        )
        result = tmpl.render(name="林夜")  # scene 缺失
        assert "{scene}" in result

    def test_render_no_variables_listed(self):
        """变量列表为空时，format 仍可使用任意变量"""
        tmpl = PromptTemplate(
            name="test",
            template="测试：{key}",
        )
        result = tmpl.render(key="value")
        assert result == "测试：value"

    def test_to_dict(self):
        tmpl = PromptTemplate(
            name="chapter_write",
            category="plot",
            template="写第{n}章",
            variables=["n"],
            version=2,
            tags=["writing"],
        )
        d = tmpl.to_dict()
        assert d["name"] == "chapter_write"
        assert d["category"] == "plot"
        assert d["version"] == 2
        assert d["tags"] == ["writing"]


class TestPromptWorkshop:
    def test_init_with_defaults(self):
        pw = PromptWorkshop("test_story")
        assert pw.story_id == "test_story"
        # 默认应注册了 5 个模板
        assert len(pw._templates) >= 5

    def test_register_and_get(self):
        pw = PromptWorkshop("test")
        tmpl = PromptTemplate(name="custom", template="自定义模板")
        pw.register(tmpl)
        assert pw.get("custom") is tmpl

    def test_get_nonexistent(self):
        pw = PromptWorkshop("test")
        assert pw.get("nonexistent") is None

    def test_render_existing(self):
        pw = PromptWorkshop("test")
        result = pw.render(
            "chapter_write",
            chapter=1,
            title="第一章",
            phase="opening",
            world_summary="仙侠世界",
            characters="林夜",
            context="开头",
            style="悬疑",
            hooks="古剑",
            word_count=2000,
        )
        assert result is not None
        assert "第一章" in result
        assert "林夜" in result

    def test_render_nonexistent(self):
        pw = PromptWorkshop("test")
        assert pw.render("nonexistent") is None

    def test_list_by_category(self):
        pw = PromptWorkshop("test")
        plot_templates = pw.list_by_category("plot")
        assert len(plot_templates) >= 2  # chapter_write + plot_outline

    def test_list_by_category_empty(self):
        pw = PromptWorkshop("test")
        assert pw.list_by_category("nonexistent") == []

    def test_list_all(self):
        pw = PromptWorkshop("test")
        all_templates = pw.list_all()
        assert len(all_templates) >= 5

    def test_remove_existing(self):
        pw = PromptWorkshop("test")
        pw.register(PromptTemplate(name="temp", template="临时"))
        assert pw.remove("temp") is True
        assert pw.get("temp") is None

    def test_remove_nonexistent(self):
        pw = PromptWorkshop("test")
        assert pw.remove("nonexistent") is False

    def test_compose(self):
        pw = PromptWorkshop("test")
        result = pw.compose(
            "chapter_write",
            subprompts=["plot_outline"],
            chapter=1,
            title="第一章",
            phase="opening",
            world_summary="世界",
            characters="角色",
            context="背景",
            style="风格",
            hooks="伏笔",
            word_count=1000,
            world="世界观",
            protagonist="主角",
            conflict="冲突",
            total_chapters=10,
            opening_end=3,
            dev_start=4,
            dev_end=7,
            conv_start=8,
            conv_end=9,
            finale_start=10,
        )
        assert result is not None
        assert "第一章" in result
        assert "---" in result  # 分隔符

    def test_compose_invalid_main(self):
        pw = PromptWorkshop("test")
        result = pw.compose("nonexistent", subprompts=[])
        assert result is None

    def test_to_dict(self):
        pw = PromptWorkshop("test_story")
        d = pw.to_dict()
        assert d["story_id"] == "test_story"
        assert len(d["templates"]) >= 5
        assert "plot" in d["categories"]

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "prompts.json")
            pw = PromptWorkshop("sid")
            pw.register(PromptTemplate(name="extra", template="额外模板"))
            pw.save(path)
            assert os.path.exists(path)

            loaded = PromptWorkshop.load(path)
            assert loaded.story_id == "sid"
            assert loaded.get("extra") is not None
            # 默认模板也应存在
            assert loaded.get("chapter_write") is not None

    def test_register_updates_category_index(self):
        pw = PromptWorkshop("test")
        tmpl = PromptTemplate(name="new_one", category="revise", template="修改模板")
        pw.register(tmpl)
        assert "new_one" in pw._categories["revise"]

    def test_category_index_after_remove(self):
        pw = PromptWorkshop("test")
        pw.register(PromptTemplate(name="temp", category="revise", template="临时"))
        pw.remove("temp")
        assert "temp" not in pw._categories.get("revise", [])
