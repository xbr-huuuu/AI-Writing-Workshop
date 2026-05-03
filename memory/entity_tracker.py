"""
实体注册表 —— 追踪小说中所有人名、地名、物品名及状态变化
每章提取实体，只记录变更，按需检索，防止细节丢失
"""
import json
import os
import hashlib
from datetime import datetime


class EntityTracker:
    """追踪全书命名实体，记录状态变化，只存变更"""

    def __init__(self, novel_dir: str = ""):
        self.entities: dict[str, dict] = {}       # name → {type, history: [{ch, desc}], aliases}
        self.chapter_summaries: dict[int, dict] = {}  # ch_num → {summary, entities_list}
        self._file = os.path.join(novel_dir, "entity_registry.json") if novel_dir else ""

    # ==================== 持久化 ====================

    def load(self):
        if self._file and os.path.exists(self._file):
            with open(self._file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.entities = data.get("entities", {})
                self.chapter_summaries = {int(k): v for k, v in data.get("chapter_summaries", {}).items()}

    def save(self):
        if self._file:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump({
                    "entities": self.entities,
                    "chapter_summaries": {str(k): v for k, v in self.chapter_summaries.items()},
                }, f, ensure_ascii=False, indent=2)

    # ==================== 实体更新 ====================

    def update_from_chapter(self, chapter_num: int, title: str, content: str):
        """从章节正文中提取实体并更新注册表"""

        extracted = self._extract_entities(chapter_num, title, content)
        if not extracted:
            return

        # 更新实体状态
        for ent in extracted.get("entities", []):
            name = ent.get("name", "").strip()
            if not name:
                continue
            desc = ent.get("current_state", "").strip()
            etype = ent.get("type", "未分类")

            if name in self.entities:
                existing = self.entities[name]
                # 只记录变更
                last_state = existing.get("state_history", [{}])[-1].get("description", "")
                if desc and desc != last_state:
                    existing["state_history"].append({"chapter": chapter_num, "description": desc})
            else:
                self.entities[name] = {
                    "type": etype,
                    "first_chapter": chapter_num,
                    "state_history": [{"chapter": chapter_num, "description": desc}],
                }

        # 存章节摘要和实体清单
        entity_names = [e.get("name", "") for e in extracted.get("entities", [])]
        self.chapter_summaries[chapter_num] = {
            "title": title,
            "summary": extracted.get("summary", ""),
            "events": extracted.get("events", []),
            "entities": entity_names,
        }

        self.save()

    # ==================== 上下文检索 ====================

    def get_context_for_chapter(self, chapter_num: int, chapter_title: str = "") -> str:
        """为写作新章提供相关实体状态 + 近期摘要"""

        if not self.entities:
            return ""

        # 1. 近期章节摘要（所有已写章）
        summary_parts = ["【全书章节摘要】"]
        for ch in sorted(self.chapter_summaries.keys()):
            cs = self.chapter_summaries[ch]
            summary_parts.append(f"  第{ch}章《{cs.get('title', '')}》：{cs.get('summary', '')}")
            events = cs.get("events", [])
            if events:
                summary_parts.append(f"    关键事件：{'、'.join(events)}")

        # 2. 活跃实体状态（最近出现过的实体取最新状态）
        recent_entities = self._get_recent_entities(window=5)
        if recent_entities:
            summary_parts.append("\n【活跃实体当前状态】")
            for name, info in sorted(recent_entities.items()):
                latest = info["state_history"][-1]["description"]
                changed_at = info["state_history"][-1]["chapter"]
                marker = "" if changed_at == info.get("first_chapter") else f"（第{changed_at}章更新）"
                summary_parts.append(f"  • {name}[{info['type']}]：{latest} {marker}")

        return '\n'.join(summary_parts)

    def get_all_entity_names(self) -> list[str]:
        return list(self.entities.keys())

    def _get_recent_entities(self, window: int = 5) -> dict:
        """获取最近 N 章出现过的实体及其当前状态"""
        recent_chs = sorted(self.chapter_summaries.keys())[-window:]
        recent_names = set()
        for ch in recent_chs:
            recent_names.update(self.chapter_summaries[ch].get("entities", []))
        return {name: self.entities[name] for name in recent_names if name in self.entities}

    # ==================== LLM 提取 ====================

    def _extract_entities(self, chapter_num: int, title: str, content: str) -> dict:
        """调用 LLM 从章节正文提取命名实体和摘要"""
        from agents.llm_client import llm as llm_client

        text = content[:5000]
        known = list(self.entities.keys())

        system = """你是一位专业的小说编辑助手。请从给定章节中提取所有命名实体和事件。

以JSON格式输出：
{
  "summary": "本章摘要（300字以内，包含关键情节转折和情感高点）",
  "events": ["事件1", "事件2", "事件3"],
  "entities": [
    {
      "name": "实体名称（人物/地点/物品/组织/概念）",
      "type": "人物/地点/物品/组织/概念",
      "current_state": "当前状态描述（50字以内，客观陈述）"
    }
  ]
}

提取规则：
- 每个有名字的人物、地点、关键物品、组织都要提取
- current_state要写当前的最新状态，不是历史
- 如果实体在前几章已出现过，current_state写本章中的状态（可能变了也可能没变）
- 只提取本章实际出现的实体"""

        known_str = f"\n已知实体（可能有变化）：{', '.join(known)}" if known else ""

        user = f"""第{chapter_num}章《{title}》
{known_str}

正文：
---
{text}
---

请提取实体和摘要："""

        try:
            resp = llm_client.chat(system=system, user=user, temperature=0.3, max_tokens=3000)
            return self._parse_json(resp)
        except Exception:
            return {}

    @staticmethod
    def _parse_json(text: str) -> dict:
        import re as _re
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
        text = _re.sub(r',\s*(\}|\])', r'\1', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
