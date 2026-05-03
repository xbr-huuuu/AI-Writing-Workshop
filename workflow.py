"""
主工作流引擎 —— 编排架构师 → 作家 → 批评家 → 修订者 → 自我反思 的完整循环
这是整个系统的"指挥中心"
"""
import json
import os
import time
from typing import Optional
from config import config
from agents.architect import ArchitectAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent
from agents.reviser import ReviserAgent
from memory.experience_log import ExperienceLog
from memory.dynamic_fewshot import fewshot, DynamicFewShot
from memory.consistency_tracker import ConsistencyTracker
from memory.entity_tracker import EntityTracker


class WritingWorkflow:
    """
    小说写作工作流
    ┌─────────────────────────────────────────────────────┐
    │  架构师 → 作家 → 批评家 → 修订者 → 自我反思 → 存档  │
    │    ↑                                       ↓       │
    │    └────────── 经验库反馈 ──────────────────┘       │
    └─────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.architect = ArchitectAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()
        self.reviser = ReviserAgent()
        self.experience_log = ExperienceLog()
        self.fewshot_manager = fewshot
        self.consistency = None  # 惰性初始化，load_novel 时赋值
        self.entity_tracker = None  # 实体注册表，load_novel 时赋值

        self.novel_title = ""
        self.novel_genre = ""
        self.global_outline = {}
        self.chapters = []
        self.current_chapter = 0
        self._novel_dir_path = ""  # load_novel 时记录，避免路径重建不一致
        self._last_critique = {}   # 上一章批评家意见，喂给作家做改进

    # ==================== 初始化 ====================

    def init_novel(self, title: str, genre: str, premise: str, total_chapters: int = 30):
        """初始化一部新小说的创作"""
        self.novel_title = title
        self.novel_genre = genre
        self.current_chapter = 0
        self.chapters = []
        self._novel_dir_path = os.path.join(config.output_dir, self._safe_filename(title))

        print(f"\n📖 初始化小说：《{title}》")
        print(f"   类型：{genre}")
        print(f"   计划章节：{total_chapters}")
        print(f"\n🧠 架构师正在设计全局大纲...")

        self.global_outline = self.architect.design_novel_outline(
            novel_title=title,
            novel_genre=genre,
            premise=premise,
            total_chapters=total_chapters,
        )

        self._save_outline()
        print(f"   ✓ 大纲设计完成\n")
        return self.global_outline

    def load_novel(self, novel_dir: str) -> bool:
        """从已有目录加载小说进度，自动检测并修复幽灵章节"""
        self._novel_dir_path = novel_dir
        outline_path = os.path.join(novel_dir, "outline.json")
        chapters_path = os.path.join(novel_dir, "chapters.json")

        if not os.path.exists(outline_path):
            print(f"✗ 未找到大纲文件：{outline_path}")
            return False

        with open(outline_path, "r", encoding="utf-8") as f:
            self.global_outline = json.load(f)

        self.novel_title = self.global_outline.get("novel_title", "")
        self.novel_genre = self.global_outline.get("genre", "")

        if os.path.exists(chapters_path):
            with open(chapters_path, "r", encoding="utf-8") as f:
                meta_chapters = json.load(f)
            # 按章节号排序
            meta_chapters.sort(key=lambda c: c["number"])
            # 只保留连续章节（从1开始无间断）
            valid = []
            ghosts = []
            expected = 1
            for ch in meta_chapters:
                ch_file = os.path.join(novel_dir, f"chapter_{ch['number']:03d}.txt")
                if ch["number"] == expected and os.path.exists(ch_file):
                    valid.append(ch)
                    expected += 1
                else:
                    ghosts.append(ch["number"])
            if ghosts:
                print(f"⚠ 检测到 {len(ghosts)} 个异常章节（第{', '.join(map(str, ghosts))}章），已自动回退")
            self.chapters = valid
            self.current_chapter = len(self.chapters)

        # v2：初始化一致性追踪器 + 实体注册表
        self.consistency = ConsistencyTracker(novel_dir=novel_dir)
        self.consistency.load()
        self.entity_tracker = EntityTracker(novel_dir=novel_dir)
        self.entity_tracker.load()

        # 回填：已有章节但实体库为空 → 自动从已有章节提取
        if self.chapters and not self.entity_tracker.entities:
            print("   📇 首次加载，正在回填已有章节的实体...")
            self._backfill_entity_tracker()

        print(f"📂 已加载：《{self.novel_title}》")
        print(f"   已完成：{self.current_chapter} 章")
        if self.entity_tracker and self.entity_tracker.entities:
            print(f"   实体注册表：{len(self.entity_tracker.entities)} 个命名实体")
        if self.consistency:
            stats = self.consistency.stats()
            if stats["total"] > 0:
                print(f"   伏笔回收：{stats['rate']}")
        return True

    # ==================== 核心循环 ====================

    def write_next_chapter(self, chapter_title: Optional[str] = None) -> dict:
        """
        执行一次完整的写作循环：写一章。
        这是系统的核心方法。
        """
        chapter_num = self.current_chapter + 1

        # 从大纲获取章节信息
        outline_chapters = self.global_outline.get("chapters", [])
        chapter_info = {}
        if chapter_num <= len(outline_chapters):
            chapter_info = outline_chapters[chapter_num - 1]
        chapter_title = chapter_title or chapter_info.get("title", f"第{chapter_num}章")

        print(f"\n{'='*50}")
        print(f"✍️  第{chapter_num}章：{chapter_title}")
        print(f"{'='*50}")

        # 获取前情摘要
        previous_summary = self._get_previous_summary()

        # 获取进化信号
        learning_signal = self.fewshot_manager.get_learning_signal()
        if learning_signal:
            print(f"   📡 {learning_signal.strip()[:100]}...")

        # STEP 1: 架构师设计
        print(f"\n🏗️  [1/5] 架构师设计结构...")
        architecture = self.architect.design_chapter(
            novel_title=self.novel_title,
            novel_genre=self.novel_genre,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            previous_summary=previous_summary,
            novel_outline=json.dumps(self.global_outline, ensure_ascii=False)[:1500],
        )
        print(f"   ✓ 结构设计完成")

        # v2：从架构中提取新伏笔
        if self.consistency:
            self._track_foreshadowing(chapter_num, architecture)
            self.consistency.snapshot_character("第{}章完成".format(chapter_num),
                {"章节号": chapter_num, "标题": chapter_title})

        # STEP 2: 作家写作
        print(f"\n✍️  [2/5] 作家创作初稿...")
        last_issues = self._last_critique.get("weaknesses", [])
        if last_issues:
            print(f"   📋 上章批评家意见已载入（{'、'.join(last_issues[:2])}）")
        # 注入实体注册表上下文
        entity_ctx = ""
        if self.entity_tracker:
            entity_ctx = self.entity_tracker.get_context_for_chapter(chapter_num, chapter_title)
            if entity_ctx:
                print(f"   📇 实体注册表已载入（{len(self.entity_tracker.entities)}个命名实体）")
        draft = self.writer.write_chapter(
            novel_title=self.novel_title,
            novel_genre=self.novel_genre,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            architecture=architecture,
            previous_chapters_summary=previous_summary,
            previous_critique=self._last_critique,
            entity_context=entity_ctx,
        )
        content = draft["content"]
        word_count = len(content)
        print(f"   ✓ 初稿完成（{word_count}字）")

        # STEP 3: 批评家评审（v2：注入一致性检查清单）
        print(f"\n🔍 [3/5] 批评家评审...")
        checklist = self.consistency.checklist() if self.consistency else ""
        if checklist and checklist != "（暂无一致性约束）":
            print(f"   📋 一致性检查清单已加载（{len(self.consistency.open_list())}个待回收伏笔）")
        critique = self.critic.critique(
            chapter_content=content,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            architecture=architecture,
            novel_genre=self.novel_genre,
            style_fingerprint=draft.get("style_fingerprint", {}),
            consistency_checklist=checklist,  # v2
        )
        score = critique.get("overall_score", "?")
        self._last_critique = critique  # 存下来喂给下一章作家
        print(f"   ✓ 评审完成 —— 总分：{score}/10")

        # v2：将批评家发现的一致性问题喂入追踪器
        if self.consistency:
            issues = critique.get("consistency_issues", [])
            for issue in issues:
                if isinstance(issue, str) and issue.strip():
                    self.consistency.plant(chapter_num, f"[批评家标记] {issue}")

        # 显示评审摘要
        if not critique.get("parse_error"):
            print(f"   优点：{', '.join(critique.get('strengths', [])[:2])}")
            print(f"   待改进：{', '.join(critique.get('weaknesses', [])[:2])}")

        # STEP 4: 修订者修改（v2：修订上限，只改最严重问题）
        print(f"\n🔧 [4/5] 修订者修改...")
        revision = self.reviser.revise(
            original_content=content,
            critique=critique,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
        )
        final_content = revision["revised_content"]
        fixed = len(revision.get("changes_made", []))
        skipped = len(revision.get("skipped", []))
        print(f"   ✓ 修订完成（修改{fixed}条，有意跳过{skipped}条minor问题）")

        # STEP 5: 自我反思 & 经验存档
        print(f"\n💾 [5/5] 自我反思 & 存档...")
        experience = self.experience_log.reflect_and_log(
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            final_content=final_content,
            critique=critique,
            architecture=architecture,
            style_fingerprint=draft.get("style_fingerprint", {}),
        )
        print(f"   ✓ 经验已存入进化库")

        # v2: 生成章节摘要（供后续章节引用，解决跨章联通问题）
        chapter_summary = self._generate_summary(chapter_num, chapter_title, final_content)

        # 保存章节（先写正文文件，再更新元数据，防止崩了丢章节）
        chapter_record = {
            "number": chapter_num,
            "title": chapter_title,
            "content": final_content,
            "critique_score": score,
            "architecture": architecture,
            "reflection": experience.get("reflection", {}),
            "timestamp": experience.get("timestamp", ""),
            "summary": chapter_summary,
        }
        self.chapters.append(chapter_record)
        self._save_single_chapter(chapter_record)  # 先写正文到磁盘
        self.current_chapter = chapter_num
        self._save_chapters_meta()                  # 再更新元数据索引
        if self.consistency:
            self.consistency.save()
        if self.entity_tracker:
            self.entity_tracker.update_from_chapter(chapter_num, chapter_title, final_content)

        # 显示进化报告
        print(f"\n{self.experience_log.get_evolution_report()}")

        return chapter_record

    def write_chapters(self, num: int):
        """连续写多章"""
        for _ in range(num):
            self.write_next_chapter()

    def rewrite_chapter(self, chapter_num: int):
        """重写指定章节：保留情节骨架，只优化文笔"""
        if chapter_num < 1 or chapter_num > len(self.chapters):
            print(f"✗ 章节号无效：第{chapter_num}章不存在")
            return

        ch = self.chapters[chapter_num - 1]
        title = ch.get("title", f"第{chapter_num}章")

        # 读原稿
        filepath = os.path.join(self._novel_dir(), f"chapter_{chapter_num:03d}.txt")
        if not os.path.exists(filepath):
            print(f"✗ 正文文件不存在：{filepath}")
            return
        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        # 获取大纲中本章的 synopsis
        outline_chapters = self.global_outline.get("chapters", [])
        synopsis = ""
        if chapter_num <= len(outline_chapters):
            synopsis = outline_chapters[chapter_num - 1].get("synopsis", "")

        # 获取上下文（前几章全文 + 实体注册表）
        ctx = self._get_previous_summary()
        entity_ctx = ""
        if self.entity_tracker:
            entity_ctx = self.entity_tracker.get_context_for_chapter(chapter_num, title)

        print(f"\n🔧 重写第{chapter_num}章《{title}》")
        print(f"   保留情节：{synopsis[:80]}...")

        # 调用作家重写
        from agents.llm_client import llm as llm_client

        system = f"""你是一位小说润色师。请优化以下章节的写作质量，但严格保留原有的情节、事件和人物行为。

优化方向：
1. 增加人物对话（至少3段自然对话）
2. 改善节奏，避免连续大段叙述
3. 用具体感官细节替代抽象心理描写
4. 让配角有自己的声音，不要成为作者观点的传声筒
5. 保留原文的精华段落，不要为了改而改

直接输出修改后的完整正文，不要任何说明。"""

        synopsis_block = f"\n\n【本章情节约束 —— 不可改变】\n{synopsis}" if synopsis else ""

        user = f"""第{chapter_num}章《{title}》

{ctx}

{entity_ctx}
{synopsis_block}

【原文】
---
{original}
---

请优化本章："""

        revised = llm_client.chat(system=system, user=user, temperature=0.7, max_tokens=8000)

        # 覆盖原文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(revised)

        # 更新内存中的内容
        self.chapters[chapter_num - 1]["content"] = revised

        print(f"   ✓ 第{chapter_num}章已重写（不更新注册表和一致性追踪）")

    # ==================== 辅助方法 ====================

    def _get_previous_summary(self) -> str:
        """获取前情：最近2章给完整正文，其余给摘要，确保细节不丢+总量可控"""
        if not self.chapters:
            return "（这是第一章，无前情）"

        novel_dir = self._novel_dir()
        lines = ["【前情回顾】"]

        # 倒数3章及以上：给摘要
        older = self.chapters[:-2] if len(self.chapters) > 2 else []
        for ch in older:
            s = ch.get("summary", "")
            if s:
                lines.append(f"第{ch['number']}章《{ch['title']}》摘要：{s}")

        # 最近2章：给完整正文
        recent = self.chapters[-2:] if len(self.chapters) >= 2 else self.chapters
        for ch in recent:
            content = ch.get("content", "")
            if content:
                lines.append(f"\n第{ch['number']}章《{ch['title']}》完整正文：\n{content}\n")
            else:
                lines.append(f"\n第{ch['number']}章《{ch['title']}》：（正文缺失）\n")

        return '\n'.join(lines)

    def _novel_dir(self) -> str:
        if self._novel_dir_path:
            return self._novel_dir_path
        return os.path.join(config.output_dir, self._safe_filename(self.novel_title))

    def _save_outline(self):
        """保存大纲"""
        os.makedirs(self._novel_dir(), exist_ok=True)
        path = os.path.join(self._novel_dir(), "outline.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.global_outline, f, ensure_ascii=False, indent=2)

    def _save_single_chapter(self, ch: dict):
        """保存单章正文到文件（先于元数据，崩了不会丢）"""
        os.makedirs(self._novel_dir(), exist_ok=True)
        content = ch.get("content", "")
        if not content:
            return
        filepath = os.path.join(self._novel_dir(), f"chapter_{ch['number']:03d}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"第{ch['number']}章 {ch['title']}\n")
            f.write(f"编辑评分：{ch.get('critique_score', '?')}/10\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)

    def _save_chapters_meta(self):
        """保存章节元数据索引并生成全书合订本"""
        os.makedirs(self._novel_dir(), exist_ok=True)

        # 保存元数据
        meta = [
            {
                "number": ch["number"],
                "title": ch["title"],
                "critique_score": ch.get("critique_score"),
                "timestamp": ch.get("timestamp", ""),
                "summary": ch.get("summary", ""),
            }
            for ch in self.chapters
        ]
        with open(os.path.join(self._novel_dir(), "chapters.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 生成全书合订本
        book_path = os.path.join(self._novel_dir(), f"{self._safe_filename(self.novel_title)}_全文.txt")
        with open(book_path, "w", encoding="utf-8") as f:
            f.write(f"《{self.novel_title}》\n\n")
            for ch in self.chapters:
                ch_file = os.path.join(self._novel_dir(), f"chapter_{ch['number']:03d}.txt")
                if os.path.exists(ch_file):
                    with open(ch_file, "r", encoding="utf-8") as cf:
                        f.write(cf.read())
                        f.write("\n\n")
                else:
                    f.write(f"\n{'='*50}\n")
                    f.write(f"第{ch['number']}章 {ch['title']}（正文缺失）\n")
                    f.write(f"{'='*50}\n\n")

    def _backfill_entity_tracker(self):
        """回填已有章节的实体（首次加载时调用）"""
        novel_dir = self._novel_dir()
        for ch in self.chapters:
            ch_num = ch["number"]
            ch_title = ch.get("title", "")
            filepath = os.path.join(novel_dir, f"chapter_{ch_num:03d}.txt")
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self.entity_tracker.update_from_chapter(ch_num, ch_title, content)

    def _track_foreshadowing(self, chapter_num: int, architecture: dict):
        """从架构设计中提取伏笔信息，喂入一致性追踪器"""
        if architecture.get("parse_error"):
            return
        structure = architecture.get("structure", {})
        # 结尾钩子是下一章的伏笔
        ending = structure.get("ending", {})
        hook = ending.get("hook_for_next", "")
        if hook:
            self.consistency.plant(chapter_num, f"钩子：{hook}")
        # 高潮中的关键事件也作为伏笔
        climax = structure.get("climax", {})
        desc = climax.get("description", "")
        if desc:
            self.consistency.plant(chapter_num, f"高潮伏笔：{desc}")

    def _generate_summary(self, chapter_num: int, title: str, content: str) -> str:
        """生成单章摘要（~200字），包含关键事件、人物变化、未解伏笔"""
        from agents.llm_client import llm as llm_client
        text = content[:3000]  # 前3000字足够判断关键情节
        system = "你是一位专业的小说编辑。请用200字以内总结本章的关键情节、人物变化和遗留伏笔。只输出摘要文本，不要其他内容。"
        user = f"第{chapter_num}章《{title}》\n\n{text}\n\n请用200字以内总结本章："
        try:
            return llm_client.chat(system=system, user=user, temperature=0.3, max_tokens=400)
        except Exception:
            return ""

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        import re
        return re.sub(r'[<>:"/\\|?*]', '_', name)


# 全局实例
workflow = WritingWorkflow()
