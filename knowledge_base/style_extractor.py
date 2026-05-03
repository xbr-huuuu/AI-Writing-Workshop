"""
文风提取器 —— 从文本中提取写作风格特征
用于分析用户自己的书稿或已有章节
"""
import re
from typing import Optional


def extract_text_stats(text: str) -> dict:
    """从文本中提取基础统计特征"""
    sentences = re.split(r'[。！？；\n]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    words = list(text)
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    if not sentences:
        return {}

    sentence_lengths = [len(s) for s in sentences]
    paragraph_lengths = [len(p) for p in paragraphs]

    dialogue_lines = len(re.findall(r'["""][^"""]+["'']', text))
    dialogue_lines += len(re.findall(r'「[^」]+」', text))
    dialogue_lines += len(re.findall(r'『[^』]+』', text))

    dialogue_ratio = dialogue_lines / len(sentences) if sentences else 0

    return {
        "total_chars": len(words),
        "total_sentences": len(sentences),
        "total_paragraphs": len(paragraphs),
        "avg_sentence_length": sum(sentence_lengths) / len(sentence_lengths),
        "max_sentence_length": max(sentence_lengths) if sentence_lengths else 0,
        "min_sentence_length": min(sentence_lengths) if sentence_lengths else 0,
        "avg_paragraph_length": sum(paragraph_lengths) / len(paragraph_lengths) if paragraph_lengths else 0,
        "dialogue_ratio": round(dialogue_ratio, 2),
    }


def analyze_chapter_rhythm(text: str) -> dict:
    """分析章节节奏 —— 将文本分段，计算情绪/节奏变化"""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if len(paragraphs) < 3:
        return {"rhythm_type": "uniform", "turning_points": []}

    segment_size = max(1, len(paragraphs) // 5)
    segments = []
    for i in range(0, len(paragraphs), segment_size):
        seg = '\n'.join(paragraphs[i:i + segment_size])
        stats = extract_text_stats(seg)
        segments.append({
            "position": round(i / len(paragraphs), 2),
            "char_count": stats.get("total_chars", 0),
            "avg_sentence_len": stats.get("avg_sentence_length", 0),
            "dialogue_ratio": stats.get("dialogue_ratio", 0),
        })

    # 检测节奏转折点：句子长度突变 > 30% 的位置
    turning_points = []
    for i in range(1, len(segments)):
        prev_avg = segments[i-1]["avg_sentence_len"]
        curr_avg = segments[i]["avg_sentence_len"]
        if prev_avg > 0 and abs(curr_avg - prev_avg) / prev_avg > 0.3:
            turning_points.append({
                "position": segments[i]["position"],
                "change": "shortening" if curr_avg < prev_avg else "lengthening",
            })

    return {
        "rhythm_type": "varied" if turning_points else "steady",
        "turning_points": turning_points,
        "segments": segments,
    }


def create_style_fingerprint(text: str, chapter_title: str = "") -> dict:
    """创建一份完整的文风指纹报告"""
    stats = extract_text_stats(text)
    rhythm = analyze_chapter_rhythm(text)

    return {
        "chapter": chapter_title,
        "stats": stats,
        "rhythm": rhythm,
        "summary": (
            f"本章共{stats.get('total_chars', 0)}字，"
            f"平均句长{stats.get('avg_sentence_length', 0):.0f}字，"
            f"对话占比{stats.get('dialogue_ratio', 0):.0%}，"
            f"节奏型：{rhythm['rhythm_type']}，"
            f"共{len(rhythm.get('turning_points', []))}个转折点。"
        ),
    }
