"""
写作系统配置
支持 DeepSeek / OpenAI / Anthropic Claude / 兼容 OpenAI 接口的模型
"""
import os

# 国内 HuggingFace 镜像，加速 ChromaDB 模型下载
if not os.getenv("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    # API 配置
    # DeepSeek（默认）
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # OpenAI 兼容（备用）
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL", None)

    # Anthropic Claude（备用）
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # 模型选择（DeepSeek V4 Pro）
    architect_model: str = os.getenv("ARCHITECT_MODEL", "deepseek-v4-pro")
    writer_model: str = os.getenv("WRITER_MODEL", "deepseek-v4-pro")
    critic_model: str = os.getenv("CRITIC_MODEL", "deepseek-v4-pro")
    reviser_model: str = os.getenv("REVISER_MODEL", "deepseek-v4-pro")

    # 知识库配置
    vector_db_path: str = "./data/vector_db"
    # 向量化使用 all-MiniLM-L6-v2（SentenceTransformer），见 vector_store.py

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
    # === 中国文学 ===
    {"title": "红楼梦", "author": "曹雪芹", "genre": "古典文学", "score": 9.6},
    {"title": "活着", "author": "余华", "genre": "现实主义", "score": 9.4},
    {"title": "三体", "author": "刘慈欣", "genre": "科幻", "score": 9.3},
    {"title": "围城", "author": "钱钟书", "genre": "讽刺小说", "score": 9.0},
    {"title": "平凡的世界", "author": "路遥", "genre": "现实主义", "score": 9.0},
    {"title": "骆驼祥子", "author": "老舍", "genre": "现实主义", "score": 8.7},
    {"title": "边城", "author": "沈从文", "genre": "乡土文学", "score": 8.9},
    {"title": "呐喊", "author": "鲁迅", "genre": "短篇小说集", "score": 9.2},
    {"title": "阿Q正传", "author": "鲁迅", "genre": "中篇小说", "score": 9.1},
    {"title": "家", "author": "巴金", "genre": "现实主义", "score": 8.6},
    {"title": "雷雨", "author": "曹禺", "genre": "戏剧", "score": 8.9},
    {"title": "倾城之恋", "author": "张爱玲", "genre": "爱情", "score": 8.8},
    {"title": "黄金时代", "author": "王小波", "genre": "现实主义", "score": 9.0},
    {"title": "废都", "author": "贾平凹", "genre": "现实主义", "score": 7.8},
    {"title": "呼兰河传", "author": "萧红", "genre": "乡土文学", "score": 8.9},
    {"title": "许三观卖血记", "author": "余华", "genre": "现实主义", "score": 9.2},
    {"title": "白鹿原", "author": "陈忠实", "genre": "现实主义", "score": 9.2},
    {"title": "长恨歌", "author": "王安忆", "genre": "都市文学", "score": 8.7},
    {"title": "妻妾成群", "author": "苏童", "genre": "家族叙事", "score": 8.5},
    {"title": "红高粱家族", "author": "莫言", "genre": "魔幻乡土", "score": 8.6},

    # === 外国文学 ===
    {"title": "百年孤独", "author": "加西亚·马尔克斯", "genre": "魔幻现实主义", "score": 9.3},
    {"title": "1984", "author": "乔治·奥威尔", "genre": "反乌托邦", "score": 9.3},
    {"title": "小王子", "author": "圣埃克苏佩里", "genre": "童话/哲学", "score": 9.2},
    {"title": "飘", "author": "玛格丽特·米切尔", "genre": "爱情/历史", "score": 9.3},
    {"title": "白夜行", "author": "东野圭吾", "genre": "推理/悬疑", "score": 9.2},
    {"title": "挪威的森林", "author": "村上春树", "genre": "爱情/青春", "score": 8.5},
    {"title": "杀死一只知更鸟", "author": "哈珀·李", "genre": "成长/正义", "score": 9.2},
    {"title": "老人与海", "author": "海明威", "genre": "硬汉文学", "score": 8.8},
    {"title": "局外人", "author": "加缪", "genre": "存在主义", "score": 9.0},
    {"title": "傲慢与偏见", "author": "简·奥斯汀", "genre": "爱情/社会", "score": 9.0},
    {"title": "月亮与六便士", "author": "毛姆", "genre": "理想主义", "score": 8.9},
    {"title": "了不起的盖茨比", "author": "菲茨杰拉德", "genre": "美国梦/幻灭", "score": 8.8},
    {"title": "哈利·波特与魔法石", "author": "J.K.罗琳", "genre": "奇幻", "score": 9.0},
    {"title": "追风筝的人", "author": "卡勒德·胡赛尼", "genre": "成长/救赎", "score": 8.9},
    {"title": "达芬奇密码", "author": "丹·布朗", "genre": "悬疑/惊悚", "score": 8.4},
    {"title": "麦田里的守望者", "author": "塞林格", "genre": "青春/反叛", "score": 8.6},
    {"title": "动物农场", "author": "乔治·奥威尔", "genre": "政治寓言", "score": 9.2},
    {"title": "罪与罚", "author": "陀思妥耶夫斯基", "genre": "心理小说", "score": 9.3},
    {"title": "战争与和平", "author": "托尔斯泰", "genre": "史诗巨著", "score": 9.3},
    {"title": "基督山伯爵", "author": "大仲马", "genre": "复仇/冒险", "score": 9.2},
    {"title": "霍乱时期的爱情", "author": "加西亚·马尔克斯", "genre": "爱情", "score": 9.1},
    {"title": "变形记", "author": "卡夫卡", "genre": "荒诞主义", "score": 8.9},
    {"title": "少年维特的烦恼", "author": "歌德", "genre": "书信体/爱情", "score": 8.4},
    {"title": "简爱", "author": "夏洛蒂·勃朗特", "genre": "爱情/成长", "score": 8.8},
    {"title": "呼啸山庄", "author": "艾米莉·勃朗特", "genre": "爱情/复仇", "score": 9.0},
    {"title": "悲惨世界", "author": "雨果", "genre": "史诗/救赎", "score": 9.3},
    {"title": "巴黎圣母院", "author": "雨果", "genre": "浪漫主义", "score": 9.0},
    {"title": "红与黑", "author": "司汤达", "genre": "心理小说", "score": 8.8},
    {"title": "包法利夫人", "author": "福楼拜", "genre": "现实主义", "score": 8.8},
    {"title": "雾都孤儿", "author": "狄更斯", "genre": "现实主义", "score": 8.6},
    {"title": "双城记", "author": "狄更斯", "genre": "历史小说", "score": 9.0},
    {"title": "洛丽塔", "author": "纳博科夫", "genre": "心理/争议", "score": 8.5},
    {"title": "第二十二条军规", "author": "约瑟夫·海勒", "genre": "黑色幽默", "score": 8.7},
    {"title": "情人", "author": "杜拉斯", "genre": "自传体/爱情", "score": 8.5},
    {"title": "生命中不能承受之轻", "author": "米兰·昆德拉", "genre": "哲学小说", "score": 9.0},
    {"title": "解忧杂货店", "author": "东野圭吾", "genre": "奇幻/治愈", "score": 8.6},
    {"title": "嫌疑人X的献身", "author": "东野圭吾", "genre": "推理/悬疑", "score": 9.1},
    {"title": "海边的卡夫卡", "author": "村上春树", "genre": "奇幻/成长", "score": 8.5},
    {"title": "1Q84", "author": "村上春树", "genre": "奇幻/爱情", "score": 8.3},
    {"title": "失乐园", "author": "渡边淳一", "genre": "爱情/伦理", "score": 8.0},
    {"title": "雪国", "author": "川端康成", "genre": "唯美主义", "score": 8.7},
    {"title": "罗生门", "author": "芥川龙之介", "genre": "短篇经典", "score": 8.9},

    # === 类型小说 ===
    {"title": "基地", "author": "阿西莫夫", "genre": "科幻", "score": 9.2},
    {"title": "沙丘", "author": "弗兰克·赫伯特", "genre": "科幻", "score": 9.0},
    {"title": "银河系搭车客指南", "author": "道格拉斯·亚当斯", "genre": "科幻/幽默", "score": 8.7},
    {"title": "神经漫游者", "author": "威廉·吉布森", "genre": "赛博朋克", "score": 8.6},
    {"title": "安德的游戏", "author": "奥森·斯科特·卡德", "genre": "科幻", "score": 8.8},
    {"title": "魔戒", "author": "托尔金", "genre": "奇幻", "score": 9.2},
    {"title": "冰与火之歌", "author": "乔治·马丁", "genre": "奇幻", "score": 9.4},
    {"title": "纳尼亚传奇", "author": "C.S.刘易斯", "genre": "奇幻", "score": 8.4},
    {"title": "福尔摩斯探案全集", "author": "柯南·道尔", "genre": "推理", "score": 9.3},
    {"title": "无人生还", "author": "阿加莎·克里斯蒂", "genre": "推理", "score": 9.2},
    {"title": "东方快车谋杀案", "author": "阿加莎·克里斯蒂", "genre": "推理", "score": 9.1},
    {"title": "肖申克的救赎", "author": "斯蒂芬·金", "genre": "悬疑/希望", "score": 9.3},
    {"title": "沉默的羔羊", "author": "托马斯·哈里斯", "genre": "惊悚", "score": 8.8},
    {"title": "教父", "author": "马里奥·普佐", "genre": "黑帮史诗", "score": 9.2},

    # === 非虚构 / 思想 ===
    {"title": "人类简史", "author": "尤瓦尔·赫拉利", "genre": "历史/社科", "score": 9.2},
    {"title": "枪炮、病菌与钢铁", "author": "贾雷德·戴蒙德", "genre": "人类学", "score": 8.9},
    {"title": "自私的基因", "author": "理查德·道金斯", "genre": "科普", "score": 8.8},
    {"title": "时间简史", "author": "霍金", "genre": "科普", "score": 9.1},
    {"title": "万历十五年", "author": "黄仁宇", "genre": "历史", "score": 9.1},
    {"title": "国史大纲", "author": "钱穆", "genre": "历史", "score": 9.3},
    {"title": "乡土中国", "author": "费孝通", "genre": "社会学", "score": 9.3},
    {"title": "美的历程", "author": "李泽厚", "genre": "美学", "score": 9.3},
    {"title": "苏菲的世界", "author": "乔斯坦·贾德", "genre": "哲学入门", "score": 8.7},

    # === 其他经典 ===
    {"title": "牧羊少年奇幻之旅", "author": "保罗·柯艾略", "genre": "寓言/励志", "score": 8.5},
    {"title": "偷书贼", "author": "马克斯·苏萨克", "genre": "战争/人性", "score": 8.8},
    {"title": "萤火虫之墓", "author": "野坂昭如", "genre": "战争/半自传", "score": 8.6},
    {"title": "窗边的小豆豆", "author": "黑柳彻子", "genre": "儿童/教育", "score": 8.9},
    {"title": "小妇人", "author": "路易莎·梅·奥尔科特", "genre": "家庭/成长", "score": 8.6},
    {"title": "安娜·卡列尼娜", "author": "托尔斯泰", "genre": "爱情/悲剧", "score": 9.1},
    {"title": "堂吉诃德", "author": "塞万提斯", "genre": "骑士/讽刺", "score": 9.1},
    {"title": "源氏物语", "author": "紫式部", "genre": "古典/宫廷", "score": 8.8},
    {"title": "尤利西斯", "author": "乔伊斯", "genre": "意识流", "score": 8.8},
    {"title": "追忆似水年华", "author": "普鲁斯特", "genre": "意识流", "score": 9.2},
    {"title": "卡拉马佐夫兄弟", "author": "陀思妥耶夫斯基", "genre": "哲学/宗教", "score": 9.4},
    {"title": "日瓦戈医生", "author": "帕斯捷尔纳克", "genre": "历史/爱情", "score": 8.7},
    {"title": "钢铁是怎样炼成的", "author": "奥斯特洛夫斯基", "genre": "革命/励志", "score": 8.3},
    {"title": "静静的顿河", "author": "肖洛霍夫", "genre": "史诗/战争", "score": 9.0},
    {"title": "我是猫", "author": "夏目漱石", "genre": "讽刺/幽默", "score": 8.6},
    {"title": "人间失格", "author": "太宰治", "genre": "自传体/颓废", "score": 8.7},
    {"title": "暗店街", "author": "帕特里克·莫迪亚诺", "genre": "记忆/身份", "score": 8.5},
    {"title": "不能承受的生命之轻", "author": "米兰·昆德拉", "genre": "哲学小说", "score": 9.0},
    {"title": "看不见的城市", "author": "卡尔维诺", "genre": "奇幻/哲学", "score": 9.1},
    {"title": "如果在冬夜，一个旅人", "author": "卡尔维诺", "genre": "元小说", "score": 9.0},
    {"title": "发条橙", "author": "安东尼·伯吉斯", "genre": "反乌托邦", "score": 8.4},
    {"title": "美丽新世界", "author": "赫胥黎", "genre": "反乌托邦", "score": 9.1},
    {"title": "我们", "author": "扎米亚京", "genre": "反乌托邦", "score": 8.6},
    {"title": "使女的故事", "author": "玛格丽特·阿特伍德", "genre": "反乌托邦", "score": 8.8},
]
