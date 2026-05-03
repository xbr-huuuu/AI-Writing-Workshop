"""
架构师Agent —— 负责制定章节结构和节奏
参考豆瓣Top100同类书籍的结构设计大纲
"""
from typing import Optional
from config import config
from agents.llm_client import llm
from knowledge_base.vector_store import store


class ArchitectAgent:
    """架构师：制定章节大纲和节奏设计"""

    def __init__(self):
        self.model = config.architect_model

    def design_chapter(
        self,
        novel_title: str,
        novel_genre: str,
        chapter_number: int,
        chapter_title: str,
        previous_summary: str,
        novel_outline: str,
    ) -> dict:
        """为一章设计结构大纲"""

        # 1. 从知识库检索同类书籍的结构参考
        query = f"{novel_genre} 小说 章节结构 节奏设计 {chapter_title}"
        similar_books = store.search_similar_books(query)

        # 2. 从经验库检索之前成功的结构设计
        exp_query = f"章节结构设计 {novel_genre} 大纲 节奏"
        past_experiences = store.search_experiences(exp_query)

        # 3. 构建提示词
        book_refs = self._format_book_refs(similar_books)
        exp_refs = self._format_experiences(past_experiences)

        system = f"""你是一位资深小说架构师，专精于章节结构和节奏设计。

你的设计哲学参考了以下豆瓣Top100经典作品的技法：
{book_refs}

你过去成功的设计经验：
{exp_refs}

请为给定的章节设计详细的结构大纲。你的输出必须是严格的JSON格式。"""

        user = f"""
【小说信息】
- 书名：《{novel_title}》
- 类型：{novel_genre}
- 总体大纲：{novel_outline}

【当前任务】
- 章节号：第{chapter_number}章
- 章节名：{chapter_title}
- 前情摘要：{previous_summary}

请以JSON格式输出本章的结构设计：

{{
  "chapter_number": {chapter_number},
  "chapter_title": "{chapter_title}",
  "word_count_target": {config.max_chapter_words},
  "structure": {{
    "opening": {{
      "type": "开篇方式（如：悬念切入/场景描写/对话开场/内心独白）",
      "content": "开篇具体内容描述，50字以内",
      "goal": "开篇要实现的目的"
    }},
    "acts": [
      {{
        "act_number": 1,
        "name": "幕名称",
        "position": "0-30%",
        "events": ["事件1", "事件2"],
        "goal": "这一段落的目的",
        "reference_technique": "参考了哪本书的什么技法"
      }}
    ],
    "climax": {{
      "position": "60-80%之间的具体位置",
      "description": "高潮内容描述",
      "emotional_peak": "情感高点是什么"
    }},
    "ending": {{
      "type": "结尾方式（悬念/留白/闭环/反转）",
      "hook_for_next": "为下一章埋什么钩子",
      "reference_technique": "参考了哪本书的结尾技法"
    }}
  }},
  "pacing_map": {{
    "0-25%": "节奏描述（如：缓慢铺垫，建立氛围）",
    "25-50%": "节奏描述",
    "50-75%": "节奏描述",
    "75-100%": "节奏描述"
  }},
  "style_notes": "本章写作风格提示"
}}
"""

        response = llm.chat(
            system=system,
            user=user,
            model=self.model,
            temperature=0.7,
            max_tokens=3000,
        )
        return self._parse_response(response)

    def design_novel_outline(
        self,
        novel_title: str,
        novel_genre: str,
        premise: str,
        total_chapters: int = 30,
    ) -> dict:
        """设计整本小说的全局大纲"""
        similar_books = store.search_similar_books(f"{novel_genre} 小说 整体结构 大纲")
        book_refs = self._format_book_refs(similar_books)

        system = f"""你是一位资深小说架构师。参考以下经典作品的结构技法：
{book_refs}

请为给定的小说创作前提设计完整的全局大纲。输出严格的JSON格式。"""

        user = f"""
书名：《{novel_title}》
类型：{novel_genre}
创作前提：{premise}
计划章节数：{total_chapters}

请以JSON格式输出全局大纲：
{{
  "novel_title": "{novel_title}",
  "genre": "{novel_genre}",
  "total_chapters": {total_chapters},
  "three_act_structure": {{
    "act1_setup": {{"chapters": "1-{total_chapters//4}", "goal": "..."}},
    "act2_confrontation": {{"chapters": "{total_chapters//4+1}-{3*total_chapters//4}", "goal": "..."}},
    "act3_resolution": {{"chapters": "{3*total_chapters//4+1}-{total_chapters}", "goal": "..."}}
  }},
  "main_characters": [{{"name": "...", "arc": "..."}}],
  "chapters": [{{"number": 1, "title": "...", "synopsis": "...", "milestone": "..."}}]
}}
"""

        response = llm.chat(system=system, user=user, model=self.model, temperature=0.8, max_tokens=16000)
        return self._parse_response(response)

    def _format_book_refs(self, books: list[dict]) -> str:
        if not books:
            return "（暂无参考数据，请依靠你的文学知识）"
        lines = []
        for b in books:
            meta = b.get("metadata", {})
            lines.append(
                f"- 《{meta.get('title', '?')}》（{meta.get('author', '?')}）"
                f" 豆瓣{meta.get('douban_score', '?')}分"
                f" | {meta.get('genre', '')}"
            )
        return '\n'.join(lines)

    def _format_experiences(self, exps: list[dict]) -> str:
        if not exps:
            return "（暂无自身经验，这是第一篇创作）"
        lines = []
        for e in exps:
            meta = e.get("metadata", {})
            lines.append(f"- [{meta.get('type', '')}] {meta.get('summary', '')} (评分: {meta.get('score', '?')}/10)")
        return '\n'.join(lines)

    def _parse_response(self, response: str) -> dict:
        import json
        # 尝试提取JSON块
        response = response.strip()
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response, "parse_error": True}
