#!/usr/bin/env python3
"""
AI写作系统 —— 学习豆瓣Top100写法，边写边进化

用法：
  python main.py init     初始化一部新小说
  python main.py write    写下一章
  python main.py batch N  连续写N章
  python main.py report   查看进化报告
  python main.py analyze  分析豆瓣Top100书籍（首次使用需运行）
"""
import sys
import os
from config import config, DOUBAN_TOP100
from workflow import WritingWorkflow
from knowledge_base.book_analyzer import batch_analyze_top100
from knowledge_base.vector_store import store


def show_banner():
    print("""
╔══════════════════════════════════════════════╗
║       📚 AI写作工坊                          ║
║   学习豆瓣Top100 · 多Agent协作 · 边写边进化   ║
╚══════════════════════════════════════════════╝
""")


def cmd_init():
    """初始化新小说"""
    print("\n📝 创建新小说\n")

    title = input("书名：").strip()
    genre = input("类型（如：科幻/奇幻/现实主义/悬疑）：").strip()
    premise = input("一句话前提（故事的核心设定）：").strip()
    chapters_str = input("计划章节数（默认30）：").strip()
    total_chapters = int(chapters_str) if chapters_str.isdigit() else 30

    if not title or not genre or not premise:
        print("✗ 书名、类型、前提不能为空")
        return

    wf = WritingWorkflow()
    outline = wf.init_novel(title, genre, premise, total_chapters)

    print("\n📋 全局大纲预览：")
    if outline.get("parse_error"):
        print(outline.get("raw_response", "")[:800])
    else:
        acts = outline.get("three_act_structure", {})
        for act_name, act_info in acts.items():
            print(f"  {act_name}: {act_info.get('goal', '')[:80]}")

        chapters = outline.get("chapters", [])
        if chapters:
            print(f"\n  章节规划（共{len(chapters)}章）：")
            for ch in chapters[:5]:
                print(f"    第{ch.get('number', '?')}章《{ch.get('title', '?')}》— {ch.get('synopsis', '')[:60]}")
            if len(chapters) > 5:
                print(f"    ... 还有{len(chapters)-5}章")


def cmd_write():
    """写下一章"""
    wf = WritingWorkflow()

    # 尝试加载已有小说
    novels = list_existing_novels()
    if novels:
        print("\n已有小说：")
        for i, name in enumerate(novels):
            print(f"  [{i+1}] {name}")
        choice = input("\n选择小说编号，或输入新小说名：").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(novels):
            novel_dir = os.path.join(config.output_dir, novels[int(choice)-1])
            if wf.load_novel(novel_dir):
                chapter_title = input("章节名（留空使用大纲中的标题）：").strip() or None
                wf.write_next_chapter(chapter_title)
            return

    # 否则初始化新小说
    print("未找到已有小说，请先初始化：")
    cmd_init()


def cmd_batch():
    """连续写多章"""
    wf = WritingWorkflow()
    novels = list_existing_novels()

    if not novels:
        print("未找到已有小说，请先 python main.py init")
        return

    print("\n已有小说：")
    for i, name in enumerate(novels):
        print(f"  [{i+1}] {name}")

    choice = input("\n选择小说编号：").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(novels)):
        print("无效选择")
        return

    novel_dir = os.path.join(config.output_dir, novels[int(choice)-1])
    if not wf.load_novel(novel_dir):
        return

    num_str = input("要写几章？").strip()
    num = int(num_str) if num_str.isdigit() else 1

    wf.write_chapters(num)


def cmd_report():
    """查看进化报告"""
    from memory.experience_log import ExperienceLog
    exp_log = ExperienceLog()
    print(exp_log.get_evolution_report())


def cmd_analyze():
    """分析豆瓣Top100书籍"""
    from knowledge_base.book_analyzer import get_analyzed_book_ids

    already = len(get_analyzed_book_ids())
    remaining = len(DOUBAN_TOP100) - already

    print("\n📖 豆瓣Top100书籍分析器")
    print(f"   总计 {len(DOUBAN_TOP100)} 本 | 已分析 {already} 本 | 剩余 {remaining} 本\n")

    if remaining == 0:
        print("全部书籍已分析完毕。")
        return

    limit_str = input(f"本次分析几本？（默认20，最多{remaining}）：").strip()
    limit = int(limit_str) if limit_str.isdigit() else 20

    print("\n开始分析（已分析过的自动跳过）...\n")

    from agents.llm_client import llm

    def llm_call(system, user):
        return llm.chat(system=system, user=user, temperature=0.6, max_tokens=2000)

    batch_analyze_top100(llm_call, limit=limit)
    print("\n分析完成！数据已存入向量数据库。")


def list_existing_novels() -> list[str]:
    """列出已有小说目录"""
    output_dir = config.output_dir
    if not os.path.exists(output_dir):
        return []
    return [
        d for d in os.listdir(output_dir)
        if os.path.isdir(os.path.join(output_dir, d))
        and os.path.exists(os.path.join(output_dir, d, "outline.json"))
    ]


def cmd_outline():
    """查看当前小说大纲"""
    import json
    novels = list_existing_novels()
    if not novels:
        print("未找到已有小说，请先 python main.py init")
        return

    print("\n已有小说：")
    for i, name in enumerate(novels):
        print(f"  [{i+1}] {name}")

    choice = input("\n选择小说编号：").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(novels)):
        print("无效选择")
        return

    novel_dir = os.path.join(config.output_dir, novels[int(choice)-1])
    outline_path = os.path.join(novel_dir, "outline.json")
    with open(outline_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    # 硬软约束
    hc = d.get("hard_constraints", {})
    if hc:
        print(f"\n🔒 硬约束（不可变）")
        print(f"   核心主题：{hc.get('core_theme', '')}")
        for cf in hc.get("character_fates", []):
            print(f"   {cf.get('name', '?')} → {cf.get('final_fate', '')}")

    # 章节列表
    chapters = d.get("chapters", [])
    print(f"\n📋 章节规划（共{len(chapters)}章）")
    for c in chapters:
        print(f"   第{c['number']}章《{c['title']}》— {c.get('synopsis', '')[:100]}")


def main():
    show_banner()

    if len(sys.argv) < 2:
        print("用法：")
        print("  python main.py init      初始化新小说")
        print("  python main.py write     写下一章（交互式）")
        print("  python main.py batch N   连续写N章")
        print("  python main.py report    查看进化报告")
        print("  python main.py outline   查看当前小说大纲")
        print("  python main.py analyze   分析豆瓣Top100书籍")
        print("  python main.py stats     查看知识库统计")
        return

    cmd = sys.argv[1].lower()

    if cmd == "init":
        cmd_init()
    elif cmd == "write":
        cmd_write()
    elif cmd == "batch":
        cmd_batch()
    elif cmd == "report":
        cmd_report()
    elif cmd == "outline":
        cmd_outline()
    elif cmd == "analyze":
        cmd_analyze()
    elif cmd == "stats":
        stats = store.get_experience_stats()
        book_count = store.books_collection.count()
        print(f"\n知识库统计：")
        print(f"  Top100书籍分析：{book_count} 本")
        print(f"  写作经验积累：{stats['total_experiences']} 条")
    else:
        print(f"未知命令：{cmd}")


if __name__ == "__main__":
    main()
