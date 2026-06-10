"""
集成测试：十步管线 + 所有子模块
"""

import sys
from pathlib import Path

# 确保能导入 天机
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from storycraft import (
    NarrativeStateMachine,
    NarrativePhase,
    PlotHook,
    StoryBible,
    CharacterProfile,
    Location,
    StoryPipeline,
    PipelineContext,
    QualityEngine,
    PromptWorkshop,
    NarrativeMemory,
)


def test_imports():
    """验证所有模块可正常导入"""
    assert NarrativeStateMachine is not None
    assert NarrativePhase is not None
    assert PlotHook is not None
    assert StoryBible is not None
    assert CharacterProfile is not None
    assert Location is not None
    assert StoryPipeline is not None
    assert PipelineContext is not None
    assert QualityEngine is not None
    assert PromptWorkshop is not None
    assert NarrativeMemory is not None
    print("✓ 所有模块导入成功")


def test_pipeline_full_run():
    """完整运行十步管线"""
    pipeline = StoryPipeline()

    ctx = PipelineContext(
        story_id="test_001",
        title="剑落星河",
        genre="仙侠",
        style="古典诗意",
        user_input="一个少年从凡人走向剑仙的故事",
        requirements="十章，包含修炼、冒险、成长",
    )

    ctx.plan["total_chapters"] = 10
    result = pipeline.run(ctx)

    assert result.current_step == "done"
    assert len(result.errors) == 0, f"存在错误: {result.errors}"
    assert len(result.chapters) == 10, f"预期10章，实际{len(result.chapters)}"
    assert len(result.outline) == 10
    assert len(result.quality_reports) == 10, (
        f"质检报告数量: {len(result.quality_reports)}"
    )

    # 验证每个质检报告
    for ch, report in result.quality_reports.items():
        assert report.passed is not None
        assert len(report.dimensions) == 6  # 六维

    print("✓ 完整管线运行成功")
    print(f"  章节数: {len(result.chapters)}")
    print(
        f"  质检通过: {sum(1 for r in result.quality_reports.values() if r.passed)}/{len(result.quality_reports)}"
    )


def test_pipeline_partial_run():
    """部分步骤运行"""
    pipeline = StoryPipeline()

    ctx = PipelineContext(
        story_id="test_002",
        title="推理之刃",
        genre="悬疑",
        user_input="侦探的最后一案",
    )

    # 仅运行 plan → bible → outline
    result = pipeline.run(ctx, start_step="plan", end_step="outline")

    assert result.current_step == "done"
    assert result.plan is not None
    assert result.plan.get("title") == "推理之刃"
    assert len(result.outline) > 0
    assert len(result.chapters) == 0  # write 步骤未运行

    print("✓ 部分管线运行成功")
    print(f"  大纲章节数: {len(result.outline)}")
    print(f"  未生成正文: {len(result.chapters)} (正确)")


def test_single_step():
    """独立执行单个步骤"""
    pipeline = StoryPipeline()

    ctx = PipelineContext(
        story_id="test_003",
        title="独步测试",
        genre="武侠",
    )

    # 单步：plan
    ctx = pipeline.run_single_step(ctx, "plan")
    assert ctx.current_step == "done"
    assert ctx.plan is not None

    # 单步：bible
    ctx = pipeline.run_single_step(ctx, "bible")
    assert ctx.bible is not None
    assert "独步测试" in ctx.bible.global_notes

    print("✓ 单步执行成功")


def test_custom_step():
    """注册自定义步骤替换默认"""
    pipeline = StoryPipeline()

    def my_plan_step(ctx: PipelineContext) -> PipelineContext:
        ctx.plan = {"custom": True, "title": ctx.title}
        return ctx

    pipeline.set_step("plan", my_plan_step)

    ctx = PipelineContext(title="定制小说", genre="奇幻")
    result = pipeline.run_single_step(ctx, "plan")

    assert result.plan.get("custom") is True
    print("✓ 自定义步骤注册成功")


def test_pipeline_error_handling():
    """错误步骤不会中断管线"""
    pipeline = StoryPipeline()

    def broken_step(ctx: PipelineContext) -> PipelineContext:
        raise RuntimeError("模拟错误")

    pipeline.set_step("outline", broken_step)

    ctx = PipelineContext(title="错误测试", genre="科幻")
    ctx.plan["total_chapters"] = 5

    # plan → outline(会失败) → state → ...
    result = pipeline.run(ctx, start_step="plan", end_step="polish")

    assert len(result.errors) > 0
    assert "模拟错误" in result.errors[0]
    # 虽然 outline 失败，但后续步骤继续
    assert result.current_step == "done"
    print("✓ 错误处理正确：步骤失败未中断管线")
    print(f"  捕获错误: {result.errors}")


def test_modules_interaction():
    """子模块间交互：state_machine + bible + pipeline"""
    pipeline = StoryPipeline()

    ctx = PipelineContext(
        story_id="test_interact",
        title="万物之声",
        genre="都市异能",
        user_input="能听见物体的声音",
    )
    ctx.plan["total_chapters"] = 5  # 短篇测试

    # 手动注入自定义子模块
    sm = NarrativeStateMachine(story_id="test_interact")
    bible = StoryBible(story_id="test_interact")

    # 预填一些内容
    bible.add_character(
        CharacterProfile(
            id="陈默",
            name="陈默",
            role="主角",
            personality="沉默寡言",
            arc="从孤独到连接",
        )
    )
    bible.add_location(Location(id="江城", name="江城", description="江南水乡城市"))
    bible.settings["世界观"] = "万物有灵，每件物品都有残留记忆"

    ctx.state_machine = sm
    ctx.bible = bible

    result = pipeline.run(ctx)

    assert result.current_step == "done"
    assert len(result.errors) == 0
    assert len(result.chapters) == 5

    # 验证 bible 内容反映在章节中
    for ch_text in result.chapters:
        assert "陈默" in ch_text  # 角色信息被嵌入占位章节

    # 验证状态机有进展
    assert sm.phase is not None
    print("✓ 子模块交互正确")
    print(f"  状态机阶段: {sm.phase}")


def test_memory_flow():
    """记忆模块：存储 → 召回 流程"""
    pipeline = StoryPipeline()

    memory = NarrativeMemory()

    # 模拟写入三章记忆
    for ch in range(1, 4):
        memory.store(
            memory_type="plot",
            content=f"第{ch}章：章节目录和关键事件描述",
            keywords=f"第{ch}章,剑落星河",
            chapter=ch,
            importance=7,
        )

    # 召回测试（recall_context 返回格式化字符串，非列表）
    recalls = memory.recall_context("第2章", window=2)
    assert isinstance(recalls, str)
    assert "第1章" in recalls
    assert "第2章" in recalls

    # 完整管线中记忆步骤
    ctx = PipelineContext(story_id="test_mem", title="记忆测试", genre="测试")
    ctx.memory = memory
    ctx.plan["total_chapters"] = 3
    ctx.chapters = ["第1章 开始", "第2章 发展", "第3章 结局"]

    pipeline.run(ctx, start_step="memorize", end_step="recall")

    # 验证记忆上下文
    ctx2 = PipelineContext(story_id="test_mem2", title="记忆测试2", genre="测试")
    ctx2.memory = memory  # 共享同一个 memory
    ctx2.plan["total_chapters"] = 1
    ctx2.chapters = ["第4章 新章"]
    pipeline.run(ctx2, start_step="memorize", end_step="recall")

    assert memory.count() >= 4
    print("✓ 记忆流正确")
    print(f"  总记忆数: {memory.count()}")


def test_pipeline_quality_guardrail():
    """质量门卫在管线中的集成"""
    pipeline = StoryPipeline()

    ctx = PipelineContext(
        story_id="test_quality",
        title="质量检测",
        genre="测试",
    )
    ctx.plan["total_chapters"] = 2
    ctx.chapters = [
        "这是一篇内容充实的章节。情节发展合理。人物形象丰满。",
        "第二篇章节，继续保持高质量写作。",
    ]

    result = pipeline.run(ctx, start_step="quality", end_step="quality")

    assert len(result.quality_reports) == 2
    for ch, report in result.quality_reports.items():
        print(f"  第{ch}章 六维评分:")
        for dim_name, dim in report.dimensions.items():
            print(f"    {dim_name}: {dim.score}/10 {'✓' if dim.passed else '✗'}")
            break  # 只打印第一个维度节省输出

    print("✓ 质检集成正确")


def test_pipeline_resume():
    """断点续写：从中间步骤恢复"""
    pipeline = StoryPipeline()

    ctx = PipelineContext(story_id="test_resume", title="续写测试", genre="奇幻")
    ctx.plan["total_chapters"] = 3
    ctx.chapters = ["已经写好的第一章内容。"]

    # 从 state 开始（跳过已完成的 plan/bible/outline/write）
    result = pipeline.run(ctx, start_step="state", end_step="polish")

    # 应该保留已有的第一章（可能被 pipeline 包装了章节标题），并补充后续步骤
    assert "已经写好的第一章内容。" in result.chapters[0]
    assert len(result.chapters) == 3  # 续写了 2, 3 章
    print("✓ 断点续写正确")
    print(f"  最终章节数: {len(result.chapters)}")


if __name__ == "__main__":
    test_imports()
    test_pipeline_full_run()
    test_pipeline_partial_run()
    test_single_step()
    test_custom_step()
    test_pipeline_error_handling()
    test_modules_interaction()
    test_memory_flow()
    test_pipeline_quality_guardrail()
    test_pipeline_resume()
    print("\n🎉 所有集成测试通过！")
