"""
经验日志 —— 记录AI每次写作后的反思总结
实现"边写边学"的核心组件
"""
import json
import os
import time
from datetime import datetime
from typing import Optional
from config import config
from agents.llm_client import llm
from knowledge_base.vector_store import store


class ExperienceLog:
    """写作经验积累系统 —— 每次写作后自动复盘并存储技法"""

    def __init__(self, save_dir: Optional[str] = None):
        self.save_dir = save_dir or config.experience_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.log_file = os.path.join(self.save_dir, "experience_log.jsonl")

    def reflect_and_log(
        self,
        chapter_number: int,
        chapter_title: str,
        final_content: str,
        critique: dict,
        architecture: dict,
        style_fingerprint: dict,
    ) -> dict:
        """
        自我反思循环：让AI总结本章的写作得失，
        将成功经验存入向量库以供未来检索
        """

        # 1. 自我反思
        system = """你是一位善于反思的作家。请总结你刚写完的这一章中使用的写作技巧。

请以JSON格式回答：
{
  "techniques_used": [
    {
      "name": "技法名称",
      "description": "具体怎么用的",
      "effectiveness": "效果如何（很好/一般/不理想）",
      "from_which_book": "这个技法最初从哪本经典作品中学来（如果有的话）"
    }
  ],
  "lessons_learned": "本章最大的教训或领悟",
  "what_to_reuse": "哪些做法值得在后续章节中重复使用",
  "what_to_avoid": "哪些做法应该避免",
  "style_evolution": "与之前相比，写作风格有什么变化或进步",
  "breakthrough_moment": "本章有没有灵感迸发的突破时刻？描述一下"
}
"""

        user = f"""
第{chapter_number}章《{chapter_title}》

编辑评分：{critique.get('overall_score', '?')}/10
优点：{critique.get('strengths', [])}
问题：{critique.get('weaknesses', [])}

文风统计：{json.dumps(style_fingerprint, ensure_ascii=False)[:500]}

请反思总结：
"""

        reflection = llm.chat(system=system, user=user, temperature=0.6, max_tokens=2000)
        reflection_data = self._safe_json_parse(reflection)

        # 2. 构建经验记录
        experience = {
            "timestamp": datetime.now().isoformat(),
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "genre": architecture.get("genre", ""),
            "critique_score": critique.get("overall_score", None),
            "reflection": reflection_data,
            "style_snapshot": {
                "total_chars": style_fingerprint.get("stats", {}).get("total_chars", 0),
                "avg_sentence_length": style_fingerprint.get("stats", {}).get("avg_sentence_length", 0),
                "dialogue_ratio": style_fingerprint.get("stats", {}).get("dialogue_ratio", 0),
                "rhythm_type": style_fingerprint.get("rhythm", {}).get("rhythm_type", ""),
            },
        }

        # 3. 持久化：写入JSONL文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(experience, ensure_ascii=False) + "\n")

        # 4. 索引化：存入向量库
        embedding_text = self._build_embedding_text(experience)
        store.add_experience(
            exp_id=f"exp_ch{chapter_number}_{int(time.time())}",
            experience={
                "type": "writing_experience",
                "chapter": chapter_number,
                "title": chapter_title,
                "score": critique.get("overall_score", 0),
                "summary": reflection_data.get("what_to_reuse", ""),
                "technique": json.dumps(reflection_data.get("techniques_used", []), ensure_ascii=False),
                "lesson": reflection_data.get("lessons_learned", ""),
            },
            embedding_text=embedding_text,
        )

        return experience

    def get_evolution_report(self) -> str:
        """生成写作进化报告"""
        if not os.path.exists(self.log_file):
            return "暂无写作记录，无法生成进化报告。"

        experiences = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    experiences.append(json.loads(line))

        if not experiences:
            return "暂无写作记录。"

        scores = [e.get("critique_score", 0) for e in experiences if e.get("critique_score")]
        word_counts = [e.get("style_snapshot", {}).get("total_chars", 0) for e in experiences]

        report = f"""
╔══════════════════════════════════╗
║      📊 写作进化报告             ║
╠══════════════════════════════════╣
║  总章节数：{len(experiences)}
║  平均编辑评分：{sum(scores)/len(scores):.1f}/10（共{len(scores)}章有评分）
║  评分趋势：{"↑ 上升" if len(scores) >= 2 and scores[-1] > scores[0] else "→ 稳定" if len(scores) >= 2 else "— 数据不足"}
║  累计字数：{sum(word_counts)}
║  平均每章字数：{sum(word_counts)//len(word_counts) if word_counts else 0}
╚══════════════════════════════════╝
"""
        return report

    def _build_embedding_text(self, exp: dict) -> str:
        reflection = exp.get("reflection", {})
        parts = [
            f"章节：第{exp.get('chapter_number', '?')}章 {exp.get('chapter_title', '')}",
            f"评分：{exp.get('critique_score', '?')}/10",
            f"心得：{reflection.get('lessons_learned', '')}",
            f"可复用技巧：{reflection.get('what_to_reuse', '')}",
            f"应避免：{reflection.get('what_to_avoid', '')}",
        ]
        return ' '.join(parts)

    def _safe_json_parse(self, text: str) -> dict:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print("  ⚠ 反思日志：JSON解析失败，保存原始文本")
            return {"raw_reflection": text}
