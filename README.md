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

**方式一：环境变量（推荐，不泄露Key到文件）**

**macOS / Linux / Git Bash：**
```bash
export DEEPSEEK_API_KEY="sk-你的key"
```

**Windows PowerShell：**
```powershell
$env:DEEPSEEK_API_KEY = "sk-你的key"
```

**Windows CMD：**
```cmd
set DEEPSEEK_API_KEY=sk-你的key
```

> **注意**：PowerShell 必须用 `$env:XXX` 语法，不能用 `set`（那是CMD的语法）。用错会导致 `os.getenv()` 读到空值，API调用返回 `Authentication Fails`。

**永久生效（Windows）：** 开始菜单搜索"环境变量" → 新建用户变量 → 变量名 `DEEPSEEK_API_KEY` → 值填你的Key。

**方式二：直接编辑 config.py**

修改 `config.py` 第13行，将空字符串替换为你的Key：
```python
deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "sk-你的key")
```

**支持的其他API：**

| 后端 | 环境变量 | 说明 |
|------|----------|------|
| DeepSeek（默认） | `DEEPSEEK_API_KEY` | 默认 base_url: `https://api.deepseek.com` |
| OpenAI | `OPENAI_API_KEY` | 可选设置 `OPENAI_BASE_URL` |
| Anthropic Claude | `ANTHROPIC_API_KEY` | 模型名需含 "claude" |
| 其他兼容接口 | `OPENAI_API_KEY` + `OPENAI_BASE_URL` | 如中转API、本地Ollama等 |

**自定义模型名：**
```bash
# 如果默认的 deepseek-v4-pro 不可用，可覆盖
export ARCHITECT_MODEL="deepseek-chat"
export WRITER_MODEL="deepseek-chat"
export CRITIC_MODEL="deepseek-chat"
export REVISER_MODEL="deepseek-chat"
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
| `deepseek_api_key` | `$DEEPSEEK_API_KEY` | DeepSeek API Key |
| `deepseek_base_url` | `https://api.deepseek.com` | DeepSeek API地址 |
| `architect_model` | `deepseek-v4-pro` | 架构师模型 |
| `writer_model` | `deepseek-v4-pro` | 作家模型 |
| `critic_model` | `deepseek-v4-pro` | 批评家模型 |
| `reviser_model` | `deepseek-v4-pro` | 修订者模型 |
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

## 故障排查

### API 认证失败：`Authentication Fails (governor)`

1. **先确认API Key有效**：运行诊断脚本
   ```powershell
   python check_api.py
   ```
   该脚本测试 4 种 base_url × model 组合，找出可用的配置。

2. **检查环境变量**：执行以下命令确认Key是否被正确读取
   ```powershell
   python -c "import os; print(os.getenv('DEEPSEEK_API_KEY')[:15])"
   ```
   - 如果输出为空 → 环境变量未设置或语法错误
   - PowerShell 用户：必须用 `$env:DEEPSEEK_API_KEY = "..."` 而非 `set`
   - CMD 用户：必须用 `set DEEPSEEK_API_KEY=...` 而非 `$env:`

3. **如果环境变量有效但仍失败**：可能 base_url 多了/少了 `/v1`
   - 在 PowerShell 中测试：`$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"` 或去掉 `/v1`

4. **模型名不匹配**：部分 DeepSeek 账号的 `deepseek-v4-pro` 可能映射为 `deepseek-chat`，可用 `check_api.py` 验证。

### ChromaDB 初始化失败

ChromaDB 依赖 sqlite3，Windows 上极少数情况会缺。解决方法：
```powershell
pip install chromadb --upgrade
```

### 首次运行 `analyze` 极慢

每分析一本书需调用一次LLM，10本书约 3-5 分钟。这是正常的，数据存入向量库后可以反复使用。

## License

MIT
