"""
写作系统配置
支持 OpenAI / Anthropic Claude / 本地模型
"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    # API 配置
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL", None)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # 模型选择
    architect_model: str = "claude-sonnet-4-6"       # 架构师：需要强推理
    writer_model: str = "claude-sonnet-4-6"          # 作家：需要创造力
    critic_model: str = "claude-sonnet-4-6"          # 批评家：需要分析力
    reviser_model: str = "claude-sonnet-4-6"         # 修订者：需要执行力

    # 知识库配置
    vector_db_path: str = "./data/vector_db"
    embedding_model: str = "text-embedding-3-small"  # OpenAI embedding

    # 写作参数
    max_chapter_words: int = 4000
    min_chapter_words: int = 1500
    default_temperature: float = 0.85
    critique_temperature: float = 0.3

    # 进化参数
    experience_retrieval_k: int = 5       # 每次检索的经验条数
    top100_retrieval_k: int = 3           # 每次检索的Top100参考数
    auto_save_interval: int = 1           # 每写几章自动保存一次经验

    # 输出路径
    output_dir: str = "./data/novels"
    experience_dir: str = "./data/experience"
    top100_dir: str = "./data/top100"


# 全局配置实例
config = Config()


# ============================================================
# 豆瓣Top100书籍列表（部分代表性书目）
# ============================================================
DOUBAN_TOP100 = [
    {"title": "百年孤独", "author": "加西亚·马尔克斯", "genre": "魔幻现实主义", "score": 9.3},
    {"title": "活着", "author": "余华", "genre": "现实主义", "score": 9.4},
    {"title": "三体", "author": "刘慈欣", "genre": "科幻", "score": 9.3},
    {"title": "红楼梦", "author": "曹雪芹", "genre": "古典文学", "score": 9.6},
    {"title": "1984", "author": "乔治·奥威尔", "genre": "反乌托邦", "score": 9.3},
    {"title": "围城", "author": "钱钟书", "genre": "讽刺小说", "score": 9.0},
    {"title": "小王子", "author": "圣埃克苏佩里", "genre": "童话/哲学", "score": 9.2},
    {"title": "平凡的世界", "author": "路遥", "genre": "现实主义", "score": 9.0},
    {"title": "哈利·波特", "author": "J.K.罗琳", "genre": "奇幻", "score": 9.0},
    {"title": "飘", "author": "玛格丽特·米切尔", "genre": "爱情/历史", "score": 9.3},
    {"title": "白夜行", "author": "东野圭吾", "genre": "推理/悬疑", "score": 9.2},
    {"title": "挪威的森林", "author": "村上春树", "genre": "爱情/青春", "score": 8.5},
    {"title": "杀死一只知更鸟", "author": "哈珀·李", "genre": "成长/正义", "score": 9.2},
    {"title": "老人与海", "author": "海明威", "genre": "硬汉文学", "score": 8.8},
    {"title": "局外人", "author": "加缪", "genre": "存在主义", "score": 9.0},
    {"title": "傲慢与偏见", "author": "简·奥斯汀", "genre": "爱情/社会", "score": 9.0},
    {"title": "月亮与六便士", "author": "毛姆", "genre": "理想主义", "score": 8.9},
    {"title": "骆驼祥子", "author": "老舍", "genre": "现实主义", "score": 8.7},
    {"title": "边城", "author": "沈从文", "genre": "乡土文学", "score": 8.9},
    {"title": "了不起的盖茨比", "author": "菲茨杰拉德", "genre": "美国梦/幻灭", "score": 8.8},
]
