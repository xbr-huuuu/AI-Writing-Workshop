# AI Writing Workshop (AI写作工坊)

> 学习豆瓣Top100写法 · 多Agent协作 · 边写边进化

一个基于大语言模型的多Agent写作系统。通过向量知识库学习豆瓣Top100经典书籍的写作技法，在创作过程中持续自我反思和经验积累，实现"越写越好"的进化效果。

## 核心架构

```
架构师 → 作家 → 批评家 → 修订者 → 自我反思 → 存入经验库
   ↑                                          ↓
   └────────── 经验库反馈到下一章 ───────────────┘
```

### 四个Agent

| Agent | 职责 | 参考数据 |
|-------|------|---------|
| **架构师** | 设计章节结构、节奏、大纲 | Top100同类书籍结构 + 历史成功结构 |
| **作家** | 根据大纲创作正文 | Top100文风指纹 + 已验证写作技巧 |
| **批评家** | 对标Top100标准评审打分 | Top100经典标准 + 历史评审维度 |
| **修订者** | 根据评审意见修改定稿 | 编辑的具体修改建议 |

### 进化机制

1. **自我反思循环**：每章写完自动复盘，总结"什么技巧有效？"
2. **经验向量化**：成功技法存入ChromaDB，可被未来检索
3. **动态Few-Shot**：下次写作时，优先检索自己过去高分章节的技法作为参考
4. **进化信号**：系统自动跟踪评分趋势，生成写作能力的元反馈

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API Key

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# 或 Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# 可选：自定义API地址
export OPENAI_BASE_URL="https://your-api-endpoint/v1"
```

### 3. 分析豆瓣Top100书籍（首次使用）

```bash
python main.py analyze
```

### 4. 开始写作

```bash
# 初始化新小说
python main.py init

# 逐章写作
python main.py write

# 批量写作（如连续写5章）
python main.py batch 5

# 查看进化报告
python main.py report

# 查看知识库统计
python main.py stats
```

## 配置说明

编辑 `config.py` 修改以下配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `architect_model` | `claude-sonnet-4-6` | 架构师模型 |
| `writer_model` | `claude-sonnet-4-6` | 作家模型 |
| `critic_model` | `claude-sonnet-4-6` | 批评家模型 |
| `max_chapter_words` | `4000` | 每章目标字数 |
| `experience_retrieval_k` | `5` | 每次检索的经验条数 |
| `top100_retrieval_k` | `3` | 每次检索的Top100参考数 |

## 技术栈

- **LLM**: OpenAI API / Anthropic Claude API
- **向量数据库**: ChromaDB
- **多Agent框架**: 自建编排层（可替换为AutoGen/CrewAI）
- **嵌入模型**: ChromaDB内置 all-MiniLM-L6-v2

## 项目结构

```
书/
├── config.py                    # 配置 + 豆瓣Top100书目
├── main.py                      # CLI入口
├── workflow.py                  # 核心工作流引擎
├── agents/                      # 多Agent系统
│   ├── architect.py             # 架构师Agent
│   ├── writer.py                # 作家Agent
│   ├── critic.py                # 批评家Agent
│   └── reviser.py               # 修订者Agent
├── knowledge_base/              # 知识库模块
│   ├── vector_store.py          # ChromaDB向量存储
│   ├── book_analyzer.py         # 书籍文风分析器
│   └── style_extractor.py       # 文风指纹提取器
└── memory/                      # 记忆进化模块
    ├── experience_log.py        # 经验日志系统
    └── dynamic_fewshot.py       # 动态Few-Shot检索
```

## License

MIT
