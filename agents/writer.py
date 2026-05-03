"""
作家Agent —— 根据架构师的大纲进行实际写作
融合Top100文风参考和自身成功经验
"""
from config import config
from agents.llm_client import llm
from knowledge_base.vector_store import store
from knowledge_base.style_extractor import create_style_fingerprint


class WriterAgent:
    """作家：负责实际生成小说正文"""

    def __init__(self):
        self.model = config.writer_model

    def write_chapter(
        self,
        novel_title: str,
        novel_genre: str,
        chapter_number: int,
        chapter_title: str,
        architecture: dict,
        previous_chapters_summary: str,
    ) -> dict:
        """根据架构师的大纲写作一章（多维度检索，集百家之长）"""

        # 分维度检索文风参考
        dim_queries = {
            "语言与描写": f"{novel_genre} 小说 语言风格 环境描写 意象 用词",
            "对话与人物": f"{novel_genre} 小说 对话写作 人物塑造 心理描写",
            "情感与氛围": f"{novel_genre} 小说 情感渲染 氛围营造 情绪起伏",
        }
        similar_books = self._multi_dimension_search(dim_queries)

        past_tips = store.search_experiences(f"{novel_genre} 写作技巧 描写 对话 节奏")

        system = self._build_writer_system(similar_books, past_tips, novel_title)

        user = f"""
【写作任务】
书名：《{novel_title}》 | 类型：{novel_genre}
第{chapter_number}章：{chapter_title}

【架构师的结构设计】
{self._format_architecture(architecture)}

【前情回顾】
{previous_chapters_summary}

【写作要求】
1. 严格遵循架构师的结构设计
2. 融合上述各维度参考书的技法，博采众长
3. 目标字数：{config.max_chapter_words}字左右
4. 在结尾处留下钩子，吸引读者继续阅读
5. 直接输出小说正文，不需要任何前言或后记

请开始创作：
"""

        draft = llm.chat(system=system, user=user, model=self.model, temperature=config.default_temperature, max_tokens=6000)

        # 生成文风指纹
        fingerprint = create_style_fingerprint(draft, chapter_title)

        return {
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "content": draft,
            "style_fingerprint": fingerprint,
            "references_used": similar_books,
        }

    def _multi_dimension_search(self, dim_queries: dict) -> str:
        """多维度检索：每个写作维度找最擅长的书，去重"""
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
                analysis = meta.get("style_analysis", "")[:250]
                dim_lines.append(f"    - 《{meta.get('title', '?')}》（{meta.get('author', '?')}）：{analysis}")
            if dim_lines:
                lines.append(f"  【{dim_name}】参考：")
                lines.extend(dim_lines)
        return '\n'.join(lines) if lines else "（暂无参考数据）"

    def _build_writer_system(self, book_refs: str, tips: list[dict], novel_title: str) -> str:
        parts = [f"你是一位才华横溢的小说家，正在创作《{novel_title}》。"]

        if book_refs and book_refs != "（暂无参考数据）":
            parts.append("\n请汲取以下经典作品各维度的技法，博采众长：")
            parts.append(book_refs)

        if tips:
            parts.append("\n请运用你过去总结的成功经验：")
            for t in tips:
                meta = t.get("metadata", {})
                parts.append(f"- {meta.get('summary', meta.get('technique', ''))}")

        parts.append("\n直接输出小说正文，不需要序言、说明或后记。用中文写作。")
        return '\n'.join(parts)

    def _format_architecture(self, arch: dict) -> str:
        """格式化架构设计为可读文本"""
        if arch.get("parse_error"):
            return str(arch.get("raw_response", ""))

        lines = []
        structure = arch.get("structure", {})

        opening = structure.get("opening", {})
        lines.append(f"开篇方式：{opening.get('type', '')} —— {opening.get('content', '')}")

        for act in structure.get("acts", []):
            lines.append(f"第{act.get('act_number', '')}幕({act.get('position', '')})：{' → '.join(act.get('events', []))}")

        climax = structure.get("climax", {})
        lines.append(f"高潮({climax.get('position', '')})：{climax.get('description', '')}")

        ending = structure.get("ending", {})
        lines.append(f"结尾方式：{ending.get('type', '')} | 下章钩子：{ending.get('hook_for_next', '')}")

        lines.append(f"\n风格提示：{arch.get('style_notes', '')}")
        return '\n'.join(lines)
