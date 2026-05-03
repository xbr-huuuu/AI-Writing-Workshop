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

        self.novel_title = ""
        self.novel_genre = ""
        self.global_outline = {}
        self.chapters = []
        self.current_chapter = 0

    # ==================== 初始化 ====================

    def init_novel(self, title: str, genre: str, premise: str, total_chapters: int = 30):
        """初始化一部新小说的创作"""
        self.novel_title = title
        self.novel_genre = genre
        self.current_chapter = 0
        self.chapters = []

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
        """从已有目录加载小说进度"""
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
                self.chapters = json.load(f)
            self.current_chapter = len(self.chapters)

        print(f"📂 已加载：《{self.novel_title}》")
        print(f"   已完成：{self.current_chapter} 章")
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

        # STEP 2: 作家写作
        print(f"\n✍️  [2/5] 作家创作初稿...")
        draft = self.writer.write_chapter(
            novel_title=self.novel_title,
            novel_genre=self.novel_genre,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            architecture=architecture,
            previous_chapters_summary=previous_summary,
        )
        content = draft["content"]
        word_count = len(content)
        print(f"   ✓ 初稿完成（{word_count}字）")

        # STEP 3: 批评家评审
        print(f"\n🔍 [3/5] 批评家评审...")
        critique = self.critic.critique(
            chapter_content=content,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            architecture=architecture,
            novel_genre=self.novel_genre,
            style_fingerprint=draft.get("style_fingerprint", {}),
        )
        score = critique.get("overall_score", "?")
        print(f"   ✓ 评审完成 —— 总分：{score}/10")

        # 显示评审摘要
        if not critique.get("parse_error"):
            print(f"   优点：{', '.join(critique.get('strengths', [])[:2])}")
            print(f"   待改进：{', '.join(critique.get('weaknesses', [])[:2])}")

        # STEP 4: 修订者修改
        print(f"\n🔧 [4/5] 修订者修改...")
        revision = self.reviser.revise(
            original_content=content,
            critique=critique,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
        )
        final_content = revision["revised_content"]
        print(f"   ✓ 修订完成")

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

        # 保存章节
        chapter_record = {
            "number": chapter_num,
            "title": chapter_title,
            "content": final_content,
            "critique_score": score,
            "architecture": architecture,
            "reflection": experience.get("reflection", {}),
            "timestamp": experience.get("timestamp", ""),
        }
        self.chapters.append(chapter_record)
        self.current_chapter = chapter_num
        self._save_chapters()

        # 显示进化报告
        print(f"\n{self.experience_log.get_evolution_report()}")

        return chapter_record

    def write_chapters(self, num: int):
        """连续写多章"""
        for _ in range(num):
            self.write_next_chapter()

    # ==================== 辅助方法 ====================

    def _get_previous_summary(self) -> str:
        """获取前几章的摘要（从章节文件读取正文）"""
        if not self.chapters:
            return "（这是第一章，无前情）"

        novel_dir = os.path.join(config.output_dir, self._safe_filename(self.novel_title))
        recent = self.chapters[-3:]
        lines = []
        for ch in recent:
            filepath = os.path.join(novel_dir, f"chapter_{ch['number']:03d}.txt")
            content = ""
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            content_preview = content[:200].replace('\n', ' ')
            lines.append(f"第{ch['number']}章《{ch['title']}》：{content_preview}...")
        return '\n'.join(lines)

    def _save_outline(self):
        """保存大纲"""
        novel_dir = os.path.join(config.output_dir, self._safe_filename(self.novel_title))
        os.makedirs(novel_dir, exist_ok=True)
        path = os.path.join(novel_dir, "outline.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.global_outline, f, ensure_ascii=False, indent=2)

    def _save_chapters(self):
        """保存所有章节"""
        novel_dir = os.path.join(config.output_dir, self._safe_filename(self.novel_title))
        os.makedirs(novel_dir, exist_ok=True)

        # 保存章节元数据
        meta = [
            {
                "number": ch["number"],
                "title": ch["title"],
                "critique_score": ch.get("critique_score"),
                "timestamp": ch.get("timestamp", ""),
            }
            for ch in self.chapters
        ]
        with open(os.path.join(novel_dir, "chapters.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # 保存每章全文
        for ch in self.chapters:
            content = ch.get("content")
            if not content:
                # 旧章节没有 content，从章节文件读取
                filename = f"chapter_{ch['number']:03d}.txt"
                filepath = os.path.join(novel_dir, filename)
                if os.path.exists(filepath):
                    continue  # 已有文件，跳过
                else:
                    content = "（正文丢失）"
            else:
                filename = f"chapter_{ch['number']:03d}.txt"
                filepath = os.path.join(novel_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"第{ch['number']}章 {ch['title']}\n")
                    f.write(f"编辑评分：{ch.get('critique_score', '?')}/10\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(content)

        # 保存整本书
        book_path = os.path.join(novel_dir, f"{self._safe_filename(self.novel_title)}_全文.txt")
        with open(book_path, "w", encoding="utf-8") as f:
            f.write(f"《{self.novel_title}》\n\n")
            for ch in self.chapters:
                content = ch.get("content")
                if not content:
                    ch_file = os.path.join(novel_dir, f"chapter_{ch['number']:03d}.txt")
                    if os.path.exists(ch_file):
                        with open(ch_file, "r", encoding="utf-8") as cf:
                            lines = cf.readlines()
                            # 跳过前4行标题头
                            content = "".join(lines[4:]) if len(lines) > 4 else "".join(lines)
                    else:
                        content = "（正文缺失）"
                f.write(f"\n{'='*50}\n")
                f.write(f"第{ch['number']}章 {ch['title']}\n")
                f.write(f"{'='*50}\n\n")
                f.write(content)
                f.write("\n\n")

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        import re
        return re.sub(r'[<>:"/\\|?*]', '_', name)


# 全局实例
workflow = WritingWorkflow()
