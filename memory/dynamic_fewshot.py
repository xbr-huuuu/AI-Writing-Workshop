"""
动态Few-Shot检索 —— 每次写作时自动检索最相关的成功经验
作为提示词中的"示范案例"提供给模型
"""
from typing import Optional
from knowledge_base.vector_store import store


class DynamicFewShot:
    """动态少样本管理器 —— 让AI优先参考自己过去成功的写作"""

    def __init__(self):
        pass

    def retrieve_best_examples(
        self,
        query: str,
        k: Optional[int] = None,
        min_score: float = 6.0,
    ) -> list[dict]:
        """
        检索最相关的成功写作经验。
        只返回评分 >= min_score 的高质量案例。
        """
        results = store.search_experiences(query, k=k)

        # 过滤低分经验
        filtered = []
        for r in results:
            meta = r.get("metadata", {})
            score = meta.get("score", 0)
            if isinstance(score, (int, float)) and score >= min_score:
                filtered.append(r)

        return filtered

    def format_for_prompt(self, examples: list[dict], max_per_example: int = 300) -> str:
        """将检索到的经验格式化为提示词可用的参考文本"""
        if not examples:
            return ""

        lines = ["【你过去成功的写作经验 —— 请参考以下技法】"]
        for i, ex in enumerate(examples, 1):
            meta = ex.get("metadata", {})
            doc = ex.get("document", "")
            lines.append(f"\n经验{i}（评分{meta.get('score', '?')}/10）：")
            lines.append(f"  章节：{meta.get('title', '?')}")
            lines.append(f"  概要：{meta.get('summary', '')[:max_per_example]}")
            lines.append(f"  技法：{meta.get('technique', '')[:max_per_example]}")

        return '\n'.join(lines)

    def get_learning_signal(self) -> str:
        """
        生成"学习信号"——总结AI在写作过程中的进化趋势，
        作为每次写作时的元指导。
        """
        stats = store.get_experience_stats()
        if stats["total_experiences"] == 0:
            return ""

        top_experiences = store.search_experiences("最佳写作技巧 成功经验", k=10)

        if not top_experiences:
            return ""

        # 汇总最近的高分经验
        techniques = []
        for ex in top_experiences:
            meta = ex.get("metadata", {})
            score = meta.get("score", 0)
            if isinstance(score, (int, float)) and score >= 7.0:
                techniques.append(meta.get("summary", ""))

        if not techniques:
            return ""

        signal = f"""
【进化信号】已积累{stats['total_experiences']}条写作技法，以下是验证过的高效技法：
{chr(10).join(f'• {t[:200]}' for t in techniques[:5])}

请在本次写作中优先使用这些已验证的技法。
"""
        return signal


# 全局实例
fewshot = DynamicFewShot()
