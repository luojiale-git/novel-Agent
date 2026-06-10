#!/usr/bin/env python3
"""
冒烟测试：验证 novel features 模块的工作状态。

测试项：
  1. 创建故事（含全部新字段）
  2. 列出故事
  3. 获取故事详情
  4. 更新大纲
  5. 添加世界观
  6. 添加人物（含外貌/成长弧线）
  7. 添加章节（含备注/状态）
  8. 更新章节
  9. 数据持久化（重新加载验证）
 10. 创建旧格式数据，验证自动迁移兼容
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from features.novel import manager
from features.novel.models import (
    Story,
    Chapter,
    Character,
    World,
    DimensionEntry,
    story_to_dict,
    story_from_dict,
)

# ---- 辅助 ----
PASS = 0
FAIL = 0


def check(desc: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        print(f"  [OK] {desc}")
        PASS += 1
    else:
        print(f"  [FAIL] {desc}  {detail}")
        FAIL += 1


# ---- 临时数据目录 ----
BACKUP_DIR = None  # 保存原始 data_dir


def setup_sandbox():
    """切换到临时数据目录，避免影响已有数据"""
    global BACKUP_DIR
    original = manager.DATA_DIR
    BACKUP_DIR = original
    sandbox = tempfile.mkdtemp(prefix="novel_smoke_")
    manager.DATA_DIR = Path(sandbox)
    os.makedirs(sandbox, exist_ok=True)
    print(f"[沙箱] 数据目录: {sandbox}")
    return sandbox


def teardown_sandbox():
    global BACKUP_DIR
    if manager.DATA_DIR and os.path.exists(manager.DATA_DIR):
        shutil.rmtree(manager.DATA_DIR)
    manager.DATA_DIR = BACKUP_DIR
    BACKUP_DIR = None


# ====== 测试 ======


def test_01_create_story():
    print("\n=== 1. 创建故事（含新字段）===")
    s = manager.create_story(
        title="星际迷途",
        genre="科幻",
        description="在遥远的未来，人类寻找新家园的故事。",
        author="测试作者",
        tone="冒险",
        pov="第三人称",
        target_audience="青少年及成人",
        tags=["科幻", "冒险", "太空"],
    )
    check("返回 dict 含 id", "id" in s and s["id"])
    check("标题正确", s["title"] == "星际迷途")
    check("作者正确", s["author"] == "测试作者")
    check("基调正确", s["tone"] == "冒险")
    check("视角正确", s["pov"] == "第三人称")
    check("标签正确", s["tags"] == ["科幻", "冒险", "太空"])
    check("state 存在且为 dict", isinstance(s.get("state"), dict))
    return s["id"]


def test_02_list_stories(story_id: str):
    print("\n=== 2. 列出故事 ===")
    stories = manager.list_stories()
    check("至少 1 个故事", len(stories) >= 1)
    check("返回 dict 含标题", any(s["id"] == story_id for s in stories))
    # 验证新增字段也在 list 中暴露
    s = next(x for x in stories if x["id"] == story_id)
    check("list 含 author", s.get("author") == "测试作者")
    check("list 含 tags", s.get("tags") == ["科幻", "冒险", "太空"])


def test_03_get_story(story_id: str):
    print("\n=== 3. 获取故事详情 ===")
    s = manager.get_story(story_id)
    check("故事存在", s is not None)
    check("标题正确", s["title"] == "星际迷途")
    check("包含 characters 列表", isinstance(s.get("characters"), list))
    check("包含 chapters 列表", isinstance(s.get("chapters"), list))
    check("包含 world 字典", isinstance(s.get("world"), dict))
    check("status 默认 draft", s.get("status") == "draft")
    check("target_audience 存在", s.get("target_audience") == "青少年及成人")


def test_04_set_outline(story_id: str):
    print("\n=== 4. 更新大纲 ===")
    outline_text = "第一幕：地球危机。第二幕：星际航行。第三幕：新家园。"
    result = manager.update_story(story_id, outline=outline_text)
    check("更新成功", result is not None)
    s = manager.get_story(story_id)
    check("大纲已设置", s.get("outline") == outline_text)


def test_05_update_world(story_id: str):
    print("\n=== 5. 世界观设定 ===")
    world = manager.update_world(
        story_id,
        name="仙女座星域",
        description="一个由三颗恒星组成的复杂星系",
        rules="超光速航行受暗物质风暴限制",
        background="公元2500年，地球资源枯竭",
    )
    check("世界观创建成功", world is not None)
    check("世界观名称正确", world["name"] == "仙女座星域")
    s = manager.get_story(story_id)
    w = s.get("world", {})
    check("世界观嵌入 story", w.get("name") == "仙女座星域")

    # 添加维度条目
    manager.add_world_dimension(story_id, "北境星", "寒冷荒芜的矿业星球")
    manager.add_world_dimension(story_id, "中央枢纽站", "最大的太空贸易站")
    s2 = manager.get_story(story_id)
    dims = s2.get("world", {}).get("dimensions", [])
    check("维度条目已添加", len(dims) == 2)
    check("维度名称正确", dims[0]["name"] == "北境星")


def test_06_add_character(story_id: str):
    print("\n=== 6. 添加人物 ===")
    c1 = manager.add_character(
        story_id,
        name="林北辰",
        role="主角",
        traits="勇敢、聪明、有点固执",
        background="前太空舰队飞行员，因事故退役",
        appearance="三十岁出头，短发，左眼有疤痕",
        arc="从逃避责任到承担使命",
    )
    check("人物创建成功", c1 is not None)
    check("人物名正确", c1["name"] == "林北辰")
    check("外貌存在", c1.get("appearance") == "三十岁出头，短发，左眼有疤痕")
    check("成长弧线存在", c1.get("arc") == "从逃避责任到承担使命")

    c2 = manager.add_character(
        story_id,
        name="艾琳",
        role="女主角",
        traits="冷静、理性、技术天才",
        background="空间站首席工程师",
    )
    check("第二位人物创建成功", c2 is not None)

    s = manager.get_story(story_id)
    check("故事中人物数为 2", len(s.get("characters", [])) == 2)


def test_07_add_chapter(story_id: str):
    print("\n=== 7. 添加章节 ===")
    ch1 = manager.add_chapter(
        story_id,
        title="序章：末日警报",
        content="公元2500年3月15日，联合国太空总署发出紧急通报...",
        notes="需要增加环境描写",
        status="draft",
    )
    check("章节创建成功", ch1 is not None)
    check("章节标题正确", ch1["title"] == "序章：末日警报")
    check("备注存在", ch1.get("notes") == "需要增加环境描写")
    check("状态为 draft", ch1.get("status") == "draft")
    check("字数统计 > 0", ch1.get("word_count", 0) > 0)

    ch2 = manager.add_chapter(
        story_id,
        title="第一章：离别",
        content="林北辰站在空间站的观测窗前，望着远处蔚蓝的地球...",
        status="final",
    )
    check("第二章节创建成功", ch2 is not None)
    check("状态为 final", ch2.get("status") == "final")

    s = manager.get_story(story_id)
    check("故事中章节数为 2", len(s.get("chapters", [])) == 2)
    check("chapter_count 字段同步", s.get("chapter_count") == 2)


def test_08_update_chapter(story_id: str):
    print("\n=== 8. 更新章节 ===")
    s = manager.get_story(story_id)
    ch_id = s["chapters"][0]["id"]

    updated = manager.update_chapter(
        story_id,
        ch_id,
        content="公元2500年3月15日，联合国太空总署发出了紧急通报：太阳即将进入超新星爆发期。",
        status="final",
    )
    check("章节更新成功", updated is not None)
    check("内容已更新", "超新星爆发" in updated["content"])
    check("状态已变更", updated["status"] == "final")

    s2 = manager.get_story(story_id)
    ch = next(c for c in s2["chapters"] if c["id"] == ch_id)
    check("持久化内容一致", "超新星爆发" in ch["content"])


def test_09_persistence(story_id: str):
    print("\n=== 9. 数据持久化验证 ===")
    # 模拟重新加载：重新初始化 manager
    old_dir = manager.DATA_DIR
    from features.novel import manager as m2
    import importlib

    importlib.reload(m2)
    # reload 后 DATA_DIR 不变
    m2.DATA_DIR = old_dir

    s = m2.get_story(story_id)
    check("reload 后故事存在", s is not None)
    check("作者持久化", s.get("author") == "测试作者")
    check("人物持久化", len(s.get("characters", [])) == 2)
    check("章节持久化", len(s.get("chapters", [])) == 2)
    check("世界观持久化", s.get("world", {}).get("name") == "仙女座星域")
    check("标签持久化", s.get("tags") == ["科幻", "冒险", "太空"])


def test_10_old_format_compat():
    print("\n=== 10. 旧格式兼容性 ===")
    old_data = {
        "id": "old_test_001",
        "title": "老故事",
        "genre": "奇幻",
        "description": "一个旧格式的故事",
        "outline": "大纲内容",
        "characters": [
            {"name": "老张", "role": "主角", "traits": "勇敢", "background": "猎人"},
        ],
        "chapters": [
            {"id": "ch_old_1", "title": "第一章", "content": "从前有座山..."},
        ],
        "world": {
            "name": "奇幻大陆",
            "description": "魔法世界",
        },
    }
    # 用 models 层转换 — 验证自动补齐
    story = story_from_dict(old_data)
    check("旧格式 title 正确", story.title == "老故事")
    check("旧格式字段保留", story.genre == "奇幻")
    check("自动补齐 status", story.status == "draft")
    check("自动补齐 author", story.author == "未知作者")
    check("自动补齐 tags", story.tags is not None)
    check("旧人物保留", len(story.characters) == 1)
    check("旧章节保留", len(story.chapters) == 1)
    check("自动补齐 chapter.word_count", story.chapters[0].word_count > 0)
    check("自动补齐 character.appearance", story.characters[0].appearance == "")
    check(
        "自动补齐 world.dimensions",
        story.world is not None and story.world.dimensions is not None,
    )

    # 再序列化回去，验证输出完整性
    out = story_to_dict(story)
    check("序列化含 status", "status" in out)
    check("序列化含 author", "author" in out)
    check("序列化含 tags", "tags" in out)
    check(
        "序列化 character 含 appearance", "appearance" in out.get("characters", [{}])[0]
    )


# ====== 入口 ======


def main():
    sandbox = setup_sandbox()
    try:
        sid = test_01_create_story()
        test_02_list_stories(sid)
        test_03_get_story(sid)
        test_04_set_outline(sid)
        test_05_update_world(sid)
        test_06_add_character(sid)
        test_07_add_chapter(sid)
        test_08_update_chapter(sid)
        test_09_persistence(sid)
        test_10_old_format_compat()

        print(f"\n{'=' * 40}")
        print(f"结果: {PASS} pass / {FAIL} fail")
        if FAIL == 0:
            print("[PASS] 所有冒烟测试通过！")
        else:
            print(f"[WARN] {FAIL} 个测试失败")
        return 0 if FAIL == 0 else 1
    finally:
        teardown_sandbox()


if __name__ == "__main__":
    sys.exit(main())
