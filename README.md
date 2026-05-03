# AI 写作工坊

> 让 AI 学习豆瓣 Top100 经典写法，在你的创作过程中持续进化，越写越好。

## 它解决了什么问题

直接让 AI 写小说，往往风格单一、缺乏深度、每一章质量雷同。

本系统通过四个 Agent 协作 + 向量知识库 + 自我反思循环，让 AI 在写作过程中**不断积累经验**，每写完一章就变得更懂怎么写好下一章。

## 写作流程

```
你输入：书名、类型、前提
        ↓
   🧠 架构师   →  设计30章全局大纲（硬约束/软约束分离，参考豆瓣Top100）
        ↓
   ✍️ 作家     →  写初稿（融合Top100文风和历史成功技法）
        ↓
   🔍 批评家   →  打分评审，指出具体问题 + 一致性核验（对标Top100标准）
        ↓
   🔧 修订者   →  只修最严重的3个问题，有意跳过minor（防过度优化）
        ↓
   💾 自我反思 →  总结本章技法得失 + 伏笔/角色快照存入一致性追踪器
        ↓
   📡 进化信号 →  下一章写作时，优先检索过去高分技法作为参考
```

## v2 新特性

### 硬约束 / 软约束分离
架构师设计大纲时区分不可变要素（核心主题、角色最终命运、关键情节点）和可调要素（具体路径、次要关系、呈现方式），保证故事主干不走样，细节随写作进化。

### 一致性追踪器
每章自动追踪：
- **伏笔埋设与回收**：从架构设计中提取钩子，记录预期回收章节，批评家发现的一致性问题自动入库
- **角色状态快照**：每章结束时拍摄角色性格状态，防止前后人设漂移
- **一致性检查清单**：写新章时自动加载所有未回收伏笔，作为批评家的评审约束

数据持久化到 `data/novels/书名/consistency.json`，退出不丢失。

### 修订上限
修订者每章最多修改 3 个最严重的问题（critical > major > minor），minor 级别有意跳过，防止过度优化导致文风机械。

### API 自动重试
三次指数退避重试（3s → 6s → 9s），网络抖动不丢章节进度。

## 快速开始

### 1. 装依赖

```powershell
pip install -r requirements.txt
```

### 2. 配 API Key

**临时生效（每次打开终端都要执行）：**

```powershell
# PowerShell
$env:DEEPSEEK_API_KEY = "sk-你的key"

# 验证是否生效
python -c "import os; print('OK' if os.getenv('DEEPSEEK_API_KEY') else 'FAIL')"
```

**永久生效：** 开始菜单搜"环境变量" → 新建用户变量 → 变量名 `DEEPSEEK_API_KEY` → 值填你的 Key。

> 也支持 OpenAI / Anthropic Claude / 第三方中转 API，见 [API 配置](#api-配置)。

### 3. 分析豆瓣 Top100（首次必做）

```powershell
python main.py analyze
```

系统逐本分析经典书籍的文风、结构、技法，存入向量库。分析 10 本约 3 分钟。

### 4. 创建你的小说

```powershell
python main.py init
```

按提示输入书名、类型、一句话前提、章节数，系统自动生成完整大纲。

### 5. 开始写

```powershell
python main.py write     # 写一章
python main.py batch 5   # 连续写 5 章
python main.py report    # 看进化报告
python main.py outline   # 查看大纲
```

## 命令速查

| 命令 | 做什么 | 多久用一次 |
|------|--------|-----------|
| `python main.py analyze` | 分析更多豆瓣 Top100 书 | 首次 + 想补充时 |
| `python main.py init` | 创建新小说 | 每本书一次 |
| `python main.py write` | 写下一章（交互式） | 每次写作 |
| `python main.py batch N` | 一口气写 N 章 | 想批量产出时 |
| `python main.py report` | 看进化报告（评分趋势） | 随时 |
| `python main.py outline` | 查看大纲（硬约束+章节规划） | 随时 |
| `python main.py stats` | 看知识库数据量 | 随时 |
| `python show_analysis.py 红楼梦` | 查看某本书的分析报告 | 随时 |
| `python show_analysis.py` | 浏览所有已分析书籍 | 随时 |
| `python check_api.py` | 诊断 API 连接 | 遇到认证错误时 |

## 项目结构

```
书/
├── main.py                      ← 入口，所有命令在这里
├── config.py                    ← 配置 + 豆瓣 Top100 书目
├── workflow.py                  ← 核心引擎，编排整个写作流程
├── check_api.py                 ← API 连接诊断工具
├── show_analysis.py             ← 查看豆瓣书籍分析报告
├── requirements.txt
│
├── agents/                      ← 四个写作 Agent
│   ├── architect.py             #   架构师：设计大纲和节奏
│   ├── writer.py                #   作家：生成正文
│   ├── critic.py                #   批评家：评审打分
│   └── reviser.py               #   修订者：修改定稿
│
├── knowledge_base/              ← 知识库（豆瓣书籍 + 写作经验）
│   ├── vector_store.py          #   ChromaDB 向量存储
│   ├── book_analyzer.py         #   书籍文风分析
│   └── style_extractor.py       #   文风指纹提取
│
├── memory/                      ← 记忆系统（实现"进化"）
│   ├── experience_log.py        #   自我反思 + 经验存档
│   ├── dynamic_fewshot.py       #   动态检索成功技法
│   └── consistency_tracker.py   #   伏笔/角色一致性追踪 (v2)
│
└── data/                        ← 运行中产生的数据（不提交 git）
    ├── vector_db/               #   向量数据库
    ├── novels/                  #   你的书稿
    └── experience/              #   经验日志
```

## 书稿在哪

```
data/novels/你的书名/
├── outline.json           # 全局大纲（可读的 JSON）
├── chapters.json           # 章节索引（含每章评分）
├── consistency.json        # 伏笔/角色一致性追踪 (v2)
├── chapter_001.txt         # 每章独立文件
├── chapter_002.txt
├── ...
└── 你的书名_全文.txt       # 整本合订
```

## API 配置

### 默认后端：DeepSeek

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的key"
```

### 切换到其他后端

| 后端 | 环境变量 | 额外设置 |
|------|----------|---------|
| DeepSeek | `DEEPSEEK_API_KEY` | 无 |
| OpenAI | `OPENAI_API_KEY` | 可选 `OPENAI_BASE_URL` |
| Claude | `ANTHROPIC_API_KEY` | 模型名需含 "claude" |
| 中转 API | `OPENAI_API_KEY` | 必须设 `OPENAI_BASE_URL` |

### 自定义模型名

```powershell
$env:ARCHITECT_MODEL = "你的模型"
$env:WRITER_MODEL    = "你的模型"
$env:CRITIC_MODEL    = "你的模型"
$env:REVISER_MODEL   = "你的模型"
```

## 故障排查

### 认证失败：`Authentication Fails`

1. 确认 Key 已加载：
   ```powershell
   python -c "import os; print(os.getenv('DEEPSEEK_API_KEY')[:15])"
   ```
   输出空 → PowerShell 语法错误。必须用 `$env:XXX = "..."` 不能 `set`。

2. 测试 API 连接：
   ```powershell
   python check_api.py
   ```
   会自动测试多个 base_url × model 组合，告诉你哪个能用。

3. 如果还是失败，尝试带 `/v1` 的地址：
   ```powershell
   $env:DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
   ```

### 模型下载很慢

首次运行会自动下载嵌入模型（~80MB），国内用户已配置 HuggingFace 镜像，约 4 分钟完成。如果仍然慢，手动设：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

### 大纲生成被截断

`max_tokens` 对 30 章大纲偏小，已默认为 16000。如果章节特别多（50章+），在 `agents/architect.py` 第 150 行增大 `max_tokens`。

## License

MIT
