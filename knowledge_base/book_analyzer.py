"""
书籍分析器 —— 分析书籍的结构、节奏、文风特征
"""
from typing import Optional
from config import DOUBAN_TOP100
from .vector_store import store


def get_book_info(title: str) -> Optional[dict]:
    """从Top100列表中查找书籍信息"""
    for book in DOUBAN_TOP100:
        if book["title"] == title:
            return book
    return None


def build_style_prompt(book: dict) -> str:
    """为一本书构建文风分析提示词"""
    return f"""
请深入分析《{book['title']}》（作者：{book['author']}，类型：{book['genre']}）的写作特征，从以下维度展开：

1. **叙事结构**：章节组织方式、时间线处理、视角切换频率
2. **语言风格**：用词特点、句式长度偏好、修辞手法使用频率
3. **节奏控制**：高潮设置间隔、情节推进速度、场景与总结的比例
4. **人物塑造**：对话占比、心理描写深度、人物弧光设计
5. **情感浓度**：情绪起伏曲线、留白与直白的比例
6. **标志性技巧**：该书最独特的写作技法（2-3个）

请给出具体的、可操作的分析，而不是笼统的赞美。每条分析附一个简短原文示例（如果记得的话）。
"""


def generate_book_feature(book: dict, llm_call) -> dict:
    """
    调用LLM分析一本书的文风指纹，返回结构化特征。
    llm_call: (system_prompt, user_prompt) -> str 的可调用对象
    """
    prompt = build_style_prompt(book)
    analysis = llm_call(
        system="你是一位资深的文学评论家和写作教练，擅长精确分析写作技法。请用中文回答。",
        user=prompt,
    )

    features = {
        "title": book["title"],
        "author": book["author"],
        "genre": book["genre"],
        "douban_score": book["score"],
        "style_analysis": analysis,
    }

    # 存入向量库
    embedding_text = f"《{book['title']}》 {book['author']} {book['genre']} {analysis[:500]}"
    store.add_book_features(
        book_id=f"book_{book['title'].replace(' ', '_')}",
        features=features,
        embedding_text=embedding_text,
    )

    return features


def batch_analyze_top100(llm_call, limit: int = 20):
    """批量分析Top100书籍并存入知识库"""
    for i, book in enumerate(DOUBAN_TOP100[:limit]):
        print(f"[{i+1}/{limit}] 分析《{book['title']}》...")
        try:
            generate_book_feature(book, llm_call)
            print(f"  ✓ 《{book['title']}》分析完成")
        except Exception as e:
            print(f"  ✗ 《{book['title']}》分析失败: {e}")
    print(f"\n全部完成，共分析 {limit} 本书")
