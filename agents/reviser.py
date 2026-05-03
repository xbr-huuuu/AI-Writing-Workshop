"""
修订者Agent —— 根据批评家的意见修改初稿
同时记录修改过程中习得的技巧到经验库
"""
from config import config
from agents.llm_client import llm


class ReviserAgent:
    """修订者：根据评审意见修改文稿"""

    def __init__(self):
        self.model = config.reviser_model

    def revise(
        self,
        original_content: str,
        critique: dict,
        chapter_number: int,
        chapter_title: str,
    ) -> dict:
        """根据评审意见修订章节"""

        if critique.get("parse_error"):
            return {
                "revised_content": original_content,
                "changes_made": [],
                "note": "评审解析失败，保留原稿",
            }

        system = """你是一位经验丰富的小说修订者，擅长根据编辑意见精准修改文稿。

修订原则：
1. 保留原文的优点和风格
2. 针对批评意见逐条修改
3. 修改后确保全文通顺连贯
4. 不做编辑没要求的改动
5. 直接输出修改后的完整正文，不要说明"""

        suggestions = '\n'.join(
            f"- [{s.get('location', '某处')}] {s.get('issue', '')} → {s.get('suggestion', '')}"
            for s in critique.get("specific_suggestions", [])
        )

        must_fix = '\n'.join(f"- {f}" for f in critique.get("must_fix", []))

        user = f"""
【修订任务】
第{chapter_number}章：{chapter_title}

【编辑意见摘要】
总分：{critique.get('overall_score', '?')}/10
总结：{critique.get('summary', '')}

【必须修改的问题】
{must_fix}

【具体修改建议】
{suggestions}

【原文】
---
{original_content}
---

请输出修订后的完整正文（不含任何说明）：
"""

        revised = llm.chat(system=system, user=user, model=self.model, temperature=0.7, max_tokens=6000)

        return {
            "revised_content": revised,
            "changes_made": critique.get("must_fix", []) + [
                s.get("suggestion", "") for s in critique.get("specific_suggestions", [])
            ],
            "critique_score": critique.get("overall_score", None),
        }
