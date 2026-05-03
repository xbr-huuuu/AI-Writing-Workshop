"""
批评家Agent —— 严格对标豆瓣Top100标准评审初稿
"""
import json
from config import config
from agents.llm_client import llm
from knowledge_base.vector_store import store


class CriticAgent:
    """批评家：以严苛标准评审写作质量"""

    def __init__(self):
        self.model = config.critic_model

    def critique(
        self,
        chapter_content: str,
        chapter_number: int,
        chapter_title: str,
        architecture: dict,
        novel_genre: str,
        style_fingerprint: dict,
        consistency_checklist: str = "",
    ) -> dict:
        """对一章的初稿进行评审（v2：含一致性检查）"""

        dim_queries = {
            "语言品质": f"{novel_genre} 小说 语言品质 用词精准 句式优美",
            "叙事节奏": f"{novel_genre} 小说 叙事节奏 情节推进 张弛有度",
            "人物塑造": f"{novel_genre} 小说 人物塑造 性格鲜明 对话真实",
        }
        book_refs = self._multi_dimension_search(dim_queries)
        past_critiques = store.search_experiences(f"评审标准 {novel_genre}")

        system = self._build_critic_system(book_refs, past_critiques)

        checklist_block = ""
        if consistency_checklist:
            checklist_block = f"""
【全书一致性约束】
{consistency_checklist}

评审时请逐条核验：本章是否与上述伏笔和角色约束一致？
"""

        user = f"""
【评审对象】
第{chapter_number}章：{chapter_title}
类型：{novel_genre}

【架构师的设计要求】
{json.dumps(architecture, ensure_ascii=False, indent=2)[:800]}
{checklist_block}
【当前章节文风数据】
- 总字数：{style_fingerprint.get('stats', {}).get('total_chars', '?')}
- 平均句长：{style_fingerprint.get('stats', {}).get('avg_sentence_length', '?')}字
- 对话占比：{style_fingerprint.get('stats', {}).get('dialogue_ratio', '?')}
- 节奏类型：{style_fingerprint.get('rhythm', {}).get('rhythm_type', '?')}

【待评审正文】
---
{chapter_content}
---

请以JSON格式输出评审报告（specific_suggestions 按严重程度排序，最严重的排最前）：
{{
  "overall_score": 8.5,
  "dimension_scores": {{
    "语言质量": 8.0,
    "节奏控制": 7.5,
    "人物塑造": 8.0,
    "情节推进": 8.5,
    "情感浓度": 7.0,
    "原创性": 8.0,
    "一致性": 8.0
  }},
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["问题1", "问题2"],
  "specific_suggestions": [
    {{
      "severity": "critical 或 major 或 minor",
      "location": "定位到具体段落",
      "issue": "具体问题",
      "suggestion": "修改建议",
      "reference": "参考了哪本书的技法"
    }}
  ],
  "must_fix": ["必须修改的问题（阻碍发表级别，最多3条）"],
  "nice_to_fix": ["锦上添花的建议"],
  "consistency_issues": ["与全书伏笔或角色约束不一致的地方"],
  "summary": "一句话总结评价"
}}
"""

        response = llm.chat(system=system, user=user, model=self.model, temperature=config.critique_temperature, max_tokens=6000)
        result = self._parse_response(response)
        # 截断修复：JSON解析失败时，将已返回的内容喂回去让它续写
        if result.get("parse_error") and not response.rstrip().endswith(('}', ']')):
            print("   🔄 JSON被截断，正在续写...")
            continue_prompt = f"""以下JSON在生成时被截断了，请从截断处精确续写剩余部分，直接输出被截断的JSON片段（从截断字符开始写）：

【已生成的完整部分 + 截断位置】
{response}←截断点

只输出剩余的JSON内容，不要重复已生成的部分："""
            continuation = llm.chat(
                system="你是一个JSON续写工具，从截断点精确输出剩余字符。",
                user=continue_prompt,
                temperature=0.1,
                max_tokens=3000,
            )
            response = response + continuation
            result = self._parse_response(response)
            if not result.get("parse_error"):
                print("   ✓ 续写成功")
        return result

    def _multi_dimension_search(self, dim_queries: dict) -> str:
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
                    f"    - 《{meta.get('title', '?')}》（豆瓣{meta.get('douban_score', '?')}分）"
                )
            if dim_lines:
                lines.append(f"  【{dim_name}】标准参照：")
                lines.extend(dim_lines)
        return '\n'.join(lines) if lines else "（暂无参考数据）"

    def _build_critic_system(self, book_refs: str, past: list[dict]) -> str:
        parts = [
            "你是一位严苛的文学编辑，拥有30年从业经验。",
            "你的评审标准对标豆瓣Top100经典作品的质量水平。",
            "你不会因为这是AI生成的就降低标准，相反，你会更严格。",
            "你的批评必须具体、有操作性，不能笼统。",
        ]

        if book_refs and book_refs != "（暂无参考数据）":
            parts.append("\n各维度参考标准：")
            parts.append(book_refs)

        if past:
            parts.append("\n历史评审中发现的重点关注维度：")
            for p in past:
                meta = p.get("metadata", {})
                parts.append(f"- {meta.get('summary', '')}")

        return '\n'.join(parts)

    def _parse_response(self, response: str) -> dict:
        response = response.strip()
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        else:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                response = response[start:end + 1]
        response = self._repair_json(response)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"  ⚠ 批评家：JSON解析失败({e})，将使用原始文本")
            print(f"     响应前200字: {response[:200]}")
            return {"raw_response": response, "parse_error": True}

    @staticmethod
    def _repair_json(text: str) -> str:
        import re
        text = re.sub(r',\s*(\}|\])', r'\1', text)
        # 修复截断：补全未闭合的结构
        # 移除末尾不完整的字段（截断在 key 或 value 中间）
        text = re.sub(r',\s*"[^"]*"\s*:\s*[^\}\]\s,]*$', '', text)
        text = re.sub(r',\s*"[^"]*"\s*$', '', text)
        # 补括号
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        # 检查是否在字符串内被截断
        in_string = (text.count('"') - text.count('\\"')) % 2 == 1
        if in_string:
            text += '"'
        text += ']' * open_brackets
        text += '}' * open_braces
        return text
