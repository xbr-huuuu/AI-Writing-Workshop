"""
经验日志 —— 提炼写作技法为独立卡片，按内容去重
脱离章节绑定，重写不误判，越写越精
"""
import json
import os
import hashlib
import time
from datetime import datetime
from typing import Optional
from config import config
from agents.llm_client import llm
from knowledge_base.vector_store import store


class ExperienceLog:
    """写作经验积累系统 —— 每次写作后提炼技法卡片，去重存储"""

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
        """自我反思 → 提炼技法卡片 → 去重存入向量库"""

        score = critique.get("overall_score", 0)
        if isinstance(score, str):
            score = 0

        # 1. 自我反思
        system = """你是一位善于反思的作家。请总结你刚写完的这一章中使用的写作技巧。

请以JSON格式回答：
{
  "techniques_used": [
    {
      "name": "技法名称（简短，如：科学细节情节化）",
      "description": "具体怎么用的（50-100字）",
      "effectiveness": "很好 或 一般 或 不理想",
      "category": "情节设计 或 语言风格 或 人物塑造 或 节奏控制 或 情感渲染 或 其他"
    }
  ],
  "lessons_learned": "本章最大的教训",
  "what_to_avoid": "哪些做法应该避免"
}
只输出使用过的、具体的技法，不要空泛总结。"""

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

        # 2. 提炼独立技法卡片，逐条去重写入
        techniques = reflection_data.get("techniques_used", [])
        if not isinstance(techniques, list):
            techniques = []

        saved_count = 0
        for t in techniques:
            if not isinstance(t, dict):
                continue
            name = t.get("name", "").strip()
            desc = t.get("description", "").strip()
            if not name or not desc:
                continue

            card = {
                "id": self._hash_id(name, desc),
                "type": "technique",
                "name": name,
                "description": desc,
                "effectiveness": t.get("effectiveness", ""),
                "category": t.get("category", ""),
                "score": score,
                "timestamp": datetime.now().isoformat(),
            }

            if self._exists(card["id"]):
                continue

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(card, ensure_ascii=False) + "\n")

            # 存入向量库
            store.add_experience(
                exp_id=card["id"],
                experience={
                    "type": "technique",
                    "name": name,
                    "description": desc,
                    "category": t.get("category", ""),
                    "effectiveness": t.get("effectiveness", ""),
                    "score": score,
                    "summary": desc,
                    "technique": name,
                    "lesson": reflection_data.get("lessons_learned", ""),
                    "title": chapter_title,
                },
                embedding_text=f"{name} {desc} {t.get('category', '')} {t.get('effectiveness', '')}",
            )
            saved_count += 1

        if saved_count > 0:
            print(f"   ✓ 提炼{saved_count}条新技法（已去重）")

        return {
            "timestamp": datetime.now().isoformat(),
            "reflection": reflection_data,
            "techniques_saved": saved_count,
            "score": score,
        }

    def get_evolution_report(self) -> str:
        """生成进化报告（统计技法卡片，非章节数）"""
        cards = self._load_all()
        if not cards:
            return "暂无写作经验。写几章后会自动提炼技法。"

        scores = [c.get("score", 0) for c in cards if c.get("score")]
        categories = {}
        for c in cards:
            cat = c.get("category", "其他")
            categories[cat] = categories.get(cat, 0) + 1

        cat_lines = '\n'.join(f"║    {k}：{v} 条" for k, v in sorted(categories.items(), key=lambda x: -x[1]))

        return f"""
╔══════════════════════════════════╗
║      📊 写作进化报告             ║
╠══════════════════════════════════╣
║  积累技法：{len(cards)} 条
║  平均评分：{sum(scores)/len(scores):.1f}/10（共{len(scores)}条有评分）
╠══════════════════════════════════╣
║  技法分布：
{cat_lines}
╚══════════════════════════════════╝
"""

    def count(self) -> int:
        return len(self._load_all())

    def _load_all(self) -> list[dict]:
        if not os.path.exists(self.log_file):
            return []
        cards = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        cards.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return cards

    def _exists(self, card_id: str) -> bool:
        """快速检查ID是否已存在"""
        if not os.path.exists(self.log_file):
            return False
        with open(self.log_file, "r", encoding="utf-8") as f:
            return card_id in f.read()

    @staticmethod
    def _hash_id(name: str, description: str) -> str:
        h = hashlib.md5(f"{name}|{description}".encode("utf-8")).hexdigest()[:10]
        return f"tech_{h}"

    # ==================== JSON 解析 ====================

    def _safe_json_parse(self, text: str) -> dict:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        else:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                text = text[start:end + 1]
        text = self._repair_json(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"  ⚠ 反思日志：JSON解析失败({e})，保存原始文本")
            return {"raw_reflection": text}

    @staticmethod
    def _repair_json(text: str) -> str:
        import re
        text = re.sub(r',\s*(\}|\])', r'\1', text)
        text = re.sub(r',\s*"[^"]*"\s*:\s*[^\}\]\s,]*$', '', text)
        text = re.sub(r',\s*"[^"]*"\s*$', '', text)
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        in_string = (text.count('"') - text.count('\\"')) % 2 == 1
        if in_string:
            text += '"'
        text += ']' * open_brackets
        text += '}' * open_braces
        return text
