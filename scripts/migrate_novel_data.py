#!/usr/bin/env python3
"""
迁移脚本：将旧的 novel JSON 数据迁移到统一数据模型格式。

用法：
    python scripts/migrate_novel_data.py                     # 默认从 data/novels/ 读取，原地升级
    python scripts/migrate_novel_data.py --dry-run            # 只读模式，显示变更预览
    python scripts/migrate_novel_data.py --source <路径>      # 指定数据目录

旧格式特点（迁移前）：
- story dict 没有 status / author / tone / tags 等字段
- character dict 没有 appearance / arc 字段
- chapter dict 没有 notes / word_count / status 字段
- world dict 嵌入在 story 中，没有 dimensions 字段

迁移后会自动补齐缺失字段，保证旧数据可被新 manager 正常读写。
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 确保项目根在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from features.novel.models import story_from_dict, story_to_dict


def collect_json_files(data_dir: str) -> list[str]:
    """收集 data_dir 下所有 .json 文件（单层）"""
    if not os.path.isdir(data_dir):
        return []
    return sorted(
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith(".json") and not f.startswith(".")
    )


def load_story(filepath: str) -> dict | None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"  [错误] 无法读取 {filepath}: {e}")
        return None


def needs_migration(data: dict) -> bool:
    """检查是否需要迁移"""
    # 核心判断：如果已经含 status 字段则认为是新格式
    if "status" in data:
        return False
    # 如果有 outline 字段但没 status，大概率是旧格式
    # 最可靠的判断：通过 models.py 的 story_from_dict 自动处理，
    # 这里用快速启发式检查
    return True


def dry_run_report(source_dir: str):
    """只读预览模式"""
    files = collect_json_files(source_dir)
    if not files:
        print(f"未在 {source_dir} 找到 JSON 文件。")
        return

    print(f"=== 迁移预览 (dry-run) ===")
    print(f"数据目录: {source_dir}")
    print(f"找到 {len(files)} 个文件\n")

    total_old = 0
    for fp in files:
        data = load_story(fp)
        if data is None:
            continue
        name = data.get("title", os.path.basename(fp))
        if needs_migration(data):
            total_old += 1
            chars_old = len(data.get("characters", []))
            chapters_old = len(data.get("chapters", []))
            has_world = bool(data.get("world"))
            print(f"  [待迁移] {name}")
            print(
                f"           人物: {chars_old}, 章节: {chapters_old}, 世界观: {has_world}"
            )
        else:
            print(f"  [已是最新] {name}")

    print(f"\n总计: {total_old} 个故事待迁移, {len(files) - total_old} 个已最新")


def do_migration(source_dir: str, backup: bool = True):
    """执行迁移"""
    files = collect_json_files(source_dir)
    if not files:
        print(f"未在 {source_dir} 找到 JSON 文件。")
        return

    print(f"=== 开始迁移 ===")
    print(f"数据目录: {source_dir}")
    print(f"备份: {'是' if backup else '否'}\n")

    migrated = 0
    failed = 0
    skipped = 0

    for fp in files:
        data = load_story(fp)
        if data is None:
            failed += 1
            continue

        name = data.get("title", os.path.basename(fp))

        if not needs_migration(data):
            print(f"  [跳过] {name} (已是最新格式)")
            skipped += 1
            continue

        # 备份原始文件
        if backup:
            backup_path = fp + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                with open(fp, "r", encoding="utf-8") as src:
                    with open(backup_path, "w", encoding="utf-8") as dst:
                        dst.write(src.read())
                print(f"  [备份] → {os.path.basename(backup_path)}")
            except IOError as e:
                print(f"  [警告] 备份失败: {e}")

        # 通过 models.py 的 story_to_dict / story_from_dict 来回转换
        # 这样 story_from_dict 会自动补齐缺失字段，story_to_dict 序列化输出
        try:
            story = story_from_dict(data)
            story_dict = story_to_dict(story)
        except Exception as e:
            print(f"  [错误] {name} 转换失败: {e}")
            failed += 1
            continue

        # 写回
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(story_dict, f, ensure_ascii=False, indent=2)
            print(f"  [已迁移] {name}")
            # 显示变更摘要
            changed = []
            if not data.get("status"):
                changed.append("+status")
            if not data.get("author"):
                changed.append("+author")
            if not data.get("tags"):
                changed.append("+tags")
            if data.get("world") and not data["world"].get("dimensions"):
                changed.append("+world.dimensions")
            for ch in data.get("chapters", []):
                if not ch.get("word_count"):
                    changed.append("+chapters[].word_count")
                    break
            for c in data.get("characters", []):
                if not c.get("appearance"):
                    changed.append("+characters[].appearance")
                    break
            if changed:
                print(f"           新增字段: {', '.join(set(changed))}")
            migrated += 1
        except IOError as e:
            print(f"  [错误] {name} 写入失败: {e}")
            failed += 1

    print(f"\n=== 迁移完成 ===")
    print(f"已迁移: {migrated}, 已跳过: {skipped}, 失败: {failed}")


def main():
    parser = argparse.ArgumentParser(description="小说数据迁移工具")
    parser.add_argument(
        "--source",
        default=os.path.join(PROJECT_ROOT, "data", "novels"),
        help="故事数据目录 (默认: data/novels/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只读预览模式，不实际修改文件",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不创建备份文件",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        print(f"数据目录不存在: {args.source}")
        print(f"提示: 将旧 JSON 文件放入 {args.source} 后重新运行。")
        sys.exit(0)

    if args.dry_run:
        dry_run_report(args.source)
    else:
        do_migration(args.source, backup=not args.no_backup)


if __name__ == "__main__":
    main()
