"""
修订者Agent —— 根据批评家的意见修改初稿（v2：修订上限，防过度优化）
同时记录修改过程中习得的技巧到经验库
"""
from config import config
from agents.llm_client import llm


class ReviserAgent:
    """修订者：根据评审意见修改文稿，只改最严重的几个问题"""

    MAX_FIXES = 3  # 修订上限：每章最多改3个问题

    def __init__(self):
        self.model = config.reviser_model

    def revise(
        self,
        original_content: str,
        critique: dict,
        chapter_number: int,
        chapter_title: str,
    ) -> dict:
        """根据评审意见修订章节（v2：只改最严重的2-3个问题）"""

        if critique.get("parse_error"):
            return {
                "revised_content": original_content,
                "changes_made": [],
                "skipped": [],
                "note": "评审解析失败，保留原稿",
            }

        # 按严重程度排序：critical > major > minor
        suggestions = critique.get("specific_suggestions", [])
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        suggestions.sort(key=lambda s: severity_order.get(s.get("severity", "minor"), 2))

        # 只取最严重的 MAX_FIXES 个
        to_fix = suggestions[:self.MAX_FIXES]
        skipped = suggestions[self.MAX_FIXES:]

        if not to_fix:
            return {
                "revised_content": original_content,
                "changes_made": [],
                "skipped": skipped,
                "note": "无critical或major级问题，保留原文",
            }

        system = """你是一位经验丰富的小说修订者，擅长精准修改而不过度干预。

修订原则：
1. 只修改下面列出的具体问题，其他内容一字不动
2. 保留原文的优点、风格和节奏
3. 修改后确保全文通顺连贯
4. 不追求完美——有些minor问题留着反而有自然感
5. 直接输出修改后的完整正文，不要说明"""

        fix_items = '\n'.join(
            f"- [{s.get('severity', '?')}] {s.get('issue', '')} → {s.get('suggestion', '')}"
            for s in to_fix
        )

        skip_items = '\n'.join(
            f"- [跳过] {s.get('issue', '')}"
            for s in skipped
        ) if skipped else "（无）"

        user = f"""
【修订任务】
第{chapter_number}章：{chapter_title}

【编辑意见摘要】
总分：{critique.get('overall_score', '?')}/10
总结：{critique.get('summary', '')}

【本次修改（只改这 {len(to_fix)} 条）】
{fix_items}

【有意跳过（保留原文）】
{skip_items}

【原文】
---
{original_content}
---

请输出修订后的完整正文（不含任何说明）：
"""

        revised = llm.chat(system=system, user=user, model=self.model, temperature=0.7, max_tokens=6000)

        return {
            "revised_content": revised,
            "changes_made": [s.get("issue", "") for s in to_fix],
            "skipped": [s.get("issue", "") for s in skipped],
            "critique_score": critique.get("overall_score", None),
        }
