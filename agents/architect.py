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
        """为一章设计结构大纲（多维度检索，集百家之长）"""

        # 分维度检索：不同书擅长不同东西
        dim_queries = {
            "开篇技法": f"{novel_genre} 小说开篇 悬念 场景切入 第一句话",
            "高潮设计": f"{novel_genre} 小说高潮 情节转折 情感峰值 冲突爆发",
            "结尾钩子": f"{novel_genre} 小说结尾 留白 悬念 章节钩子 反转",
            "节奏控制": f"{novel_genre} 小说节奏 张弛 场景转换 叙事速度",
        }
        book_refs = self._multi_dimension_search(dim_queries)

        exp_query = f"章节结构设计 {novel_genre} 大纲 节奏"
        past_experiences = store.search_experiences(exp_query)
        exp_refs = self._format_experiences(past_experiences)

        system = f"""你是一位资深小说架构师，专精于章节结构和节奏设计。

以下豆瓣Top100经典作品按维度分类的技法参考：
{book_refs}

你过去成功的设计经验：
{exp_refs}

请综合以上所有书籍的技法，融会贯通，为给定章节设计结构。输出严格的JSON格式。"""

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
        """设计整本小说的全局大纲（v2：含硬软约束，多维度检索）"""
        dim_queries = {
            "整体结构": f"{novel_genre} 小说 整体结构 三幕 叙事框架",
            "人物弧光": f"{novel_genre} 小说 人物成长 性格转变 角色命运",
            "主题呈现": f"{novel_genre} 小说 核心主题 象征 隐喻 思想深度",
        }
        book_refs = self._multi_dimension_search(dim_queries)

        system = f"""你是一位资深小说架构师。参考以下经典作品的结构技法：
{book_refs}

请为给定的小说创作前提设计完整的全局大纲。输出严格的JSON格式。

重要：请区分硬约束（不可变）和软约束（可动态调整）。
- 硬约束：核心主题、角色最终命运、关键情节点——这些是故事的脊梁
- 软约束：具体路径、次要角色关系、呈现方式——这些可以随着写作进化而调整"""

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
  "hard_constraints": {{
    "core_theme": "一句话核心主题（不可变）",
    "character_fates": [{{"name": "...", "final_fate": "角色最终结局（不可变）"}}],
    "key_milestones": ["不可变更的关键情节点1", "关键情节点2"]
  }},
  "soft_constraints": {{
    "tone_flexibility": "风格可调整的空间",
    "subplot_room": "支线可增删的范围",
    "pacing_adjustments": "节奏可快可慢的段落"
  }},
  "three_act_structure": {{
    "act1_setup": {{"chapters": "1-{total_chapters//4}", "goal": "..."}},
    "act2_confrontation": {{"chapters": "{total_chapters//4+1}-{3*total_chapters//4}", "goal": "..."}},
    "act3_resolution": {{"chapters": "{3*total_chapters//4+1}-{total_chapters}", "goal": "..."}}
  }},
  "main_characters": [{{"name": "...", "arc": "...", "core_trait": "不可变的性格底色"}}],
  "chapters": [{{"number": 1, "title": "...", "synopsis": "...", "milestone": "..."}}]
}}
"""

        response = llm.chat(system=system, user=user, model=self.model, temperature=0.8, max_tokens=16000)
        return self._parse_response(response)

    def _multi_dimension_search(self, dim_queries: dict) -> str:
        """多维度检索：每个写作维度找最擅长的书，去重后按维度组织"""
        seen_ids = set()
        lines = []
        for dim_name, query in dim_queries.items():
            books = store.search_similar_books(query, k=config.top100_retrieval_k)
            dim_lines = []
            for b in books:
                bid = b.get("id", "")
                if bid in seen_ids:
                    continue
                seen_ids.add(bid)
                meta = b.get("metadata", {})
                dim_lines.append(
                    f"    - 《{meta.get('title', '?')}》（{meta.get('author', '?')}）"
                    f" 豆瓣{meta.get('douban_score', '?')}分"
                )
            if dim_lines:
                lines.append(f"  【{dim_name}】参考：")
                lines.extend(dim_lines)
        return '\n'.join(lines) if lines else "（暂无参考数据，请依靠你的文学知识）"

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
        response = response.strip()
        # 提取 JSON 块
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        else:
            # 没有代码围栏，尝试找到最外层 JSON
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                response = response[start:end + 1]
        # 修复常见 JSON 错误
        response = self._repair_json(response)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"  ⚠ 架构师：JSON解析失败({e})，将使用原始文本")
            print(f"     响应前200字: {response[:200]}")
            return {"raw_response": response, "parse_error": True}

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
