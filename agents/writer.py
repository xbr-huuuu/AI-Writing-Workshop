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
        """根据架构师的大纲写作一章"""

        # 检索相关文风参考
        style_query = self._build_style_query(architecture, novel_genre)
        similar_books = store.search_similar_books(style_query)

        # 检索过去成功的写作技巧
        past_tips = store.search_experiences(f"{novel_genre} 写作技巧 描写 对话 节奏")

        # 构建写作提示词
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
2. 运用参考书籍的技法，但用自己的语言
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
            "references_used": [b.get("metadata", {}).get("title", "") for b in similar_books],
        }

    def _build_style_query(self, architecture: dict, genre: str) -> str:
        """从架构设计中提取风格查询词"""
        structure = architecture.get("structure", {})
        style_notes = architecture.get("style_notes", "")

        opening_type = structure.get("opening", {}).get("type", "")
        ending_type = structure.get("ending", {}).get("type", "")

        return f"{genre} {opening_type} {ending_type} {style_notes}"

    def _build_writer_system(self, books: list[dict], tips: list[dict], novel_title: str) -> str:
        parts = [f"你是一位才华横溢的小说家，正在创作《{novel_title}》。"]

        if books:
            parts.append("\n请汲取以下经典作品的技法：")
            for b in books:
                meta = b.get("metadata", {})
                analysis = meta.get("style_analysis", "")[:300]
                parts.append(f"- 《{meta.get('title', '?')}》：{analysis}")

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
