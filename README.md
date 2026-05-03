# AI 写作工坊

> 分维度检索豆瓣 Top100 技法，多 Agent 协作写作，写完一章自动提炼技法存入经验库。越写越懂怎么写。

## 核心机制

### 多维度检索：集百家之长

不同书擅长不同东西——《百年孤独》的开篇、《三体》的悬念、《雪国》的留白。系统不是一次性搜 3 本书完事，而是按写作维度分别检索：

| 写作维度 | 检索方向 | 可能搜到 |
|---------|---------|---------|
| 开篇技法 | 悬念切入、场景描写 | 《百年孤独》《1984》 |
| 高潮设计 | 情节转折、情感峰值 | 《三体》《罪与罚》 |
| 结尾钩子 | 留白、反转、章节钩子 | 《雪国》《基地》 |
| 节奏控制 | 张弛、场景转换 | 《冰与火之歌》《沙丘》 |
| 语言描写 | 用词、意象、环境 | 《红楼梦》《边城》 |
| 对话人物 | 对话写作、心理描写 | 《围城》《活着》 |

四个 Agent（架构师、作家、批评家）各自按维度检索，去重后 AI 拿到的是**按用途标注的技法参考**，而不是一堆无差别书目。

### 写作 → 反思 → 提炼 → 去重

```
写一章 → 架构师设计结构 → 作家写初稿 → 批评家评审 → 修订者修改
                                                      ↓
                                              自我反思：这章用了什么技法？
                                                      ↓
                                              拆成独立技法卡片，MD5 去重写入经验库
                                                      ↓
                                              下章写作时自动检索 → 进化
```

### 章节联通：不给碎片给全文

写第 8 章时 AI 拿到的上下文：

```
第1-5章摘要（各200字，关键情节密度高）
第6章完整正文（6000字，细节全保留）
第7章完整正文（6000字，细节全保留）
+ 一致性清单（未回收伏笔 + 角色约束）
```

最近两章给全文确保细节不丢，老章节给摘要控制总量。

### 防崩机制

- **一致性追踪**：伏笔埋设/回收 + 角色快照，防前后矛盾
- **修订上限**：每章最多改 3 个最严重问题，防过度优化
- **API 重试**：三次指数退避（3s→6s→9s），网络抖动不丢进度
- **先写正文再写元数据**：崩了也有章节文件在磁盘上

## 快速开始

### 1. 装依赖

```powershell
pip install -r requirements.txt
```

### 2. 配 API Key

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的key"
python -c "import os; print('OK' if os.getenv('DEEPSEEK_API_KEY') else 'FAIL')"
```

永久生效：系统环境变量加 `DEEPSEEK_API_KEY`。

### 3. 分析豆瓣 Top100（首次必做）

```powershell
python main.py analyze
```

逐本分析经典书籍的文风、结构、技法，存入向量库。已分析过的自动跳过。

### 4. 创建小说

```powershell
python main.py init
```

按提示输入书名、类型、一句话前提，架构师自动生成 30 章大纲（含硬约束/软约束分离）。

### 5. 开始写

```powershell
python main.py write     # 写一章
python main.py batch 5   # 连续写 5 章
python main.py report    # 看进化报告
python main.py outline   # 查看大纲
```

## 命令速查

| 命令 | 做什么 |
|------|--------|
| `python main.py init` | 创建新小说 |
| `python main.py write` | 写下一章（交互式） |
| `python main.py batch N` | 一口气写 N 章 |
| `python main.py outline` | 查看大纲（硬约束+章节规划） |
| `python main.py report` | 进化报告（技法积累+评分趋势） |
| `python main.py analyze` | 分析豆瓣 Top100 书籍 |
| `python main.py stats` | 知识库数据量 |
| `python show_analysis.py` | 浏览所有已分析书籍 |
| `python show_analysis.py 书名` | 查看某本书分析报告 |
| `python check_api.py` | 诊断 API 连接 |

## 项目结构

```
├── main.py                      ← 入口
├── config.py                    ← 配置 + 豆瓣 Top100 书目
├── workflow.py                  ← 核心引擎
├── check_api.py                 ← API 诊断
├── show_analysis.py             ← 浏览书籍分析
├── requirements.txt
│
├── agents/
│   ├── architect.py             #   架构师：多维度检索 + 结构设计
│   ├── writer.py                #   作家：多维度检索 + 正文生成
│   ├── critic.py                #   批评家：对标评审 + 一致性核验
│   ├── reviser.py               #   修订者：上限 3 条精准修改
│   └── llm_client.py            #   API 调用（自动重试）
│
├── knowledge_base/
│   ├── vector_store.py          #   ChromaDB 向量存储
│   ├── book_analyzer.py         #   豆瓣书籍分析
│   └── style_extractor.py       #   文风指纹提取
│
├── memory/
│   ├── experience_log.py        #   技法提炼 + MD5 去重
│   ├── dynamic_fewshot.py       #   动态检索成功技法
│   └── consistency_tracker.py   #   伏笔/角色一致性追踪
│
└── data/                        ← 运行数据（不提交 git）
    ├── vector_db/               #   豆瓣分析 + 经验向量
    ├── novels/                  #   书稿
    └── experience/              #   技法卡片
```

## 书稿在哪

```
data/novels/书名/
├── outline.json           # 全局大纲 + 硬软约束
├── chapters.json          # 章节索引（含摘要 + 评分）
├── consistency.json       # 伏笔/角色一致性追踪
├── chapter_001.txt        # 每章独立文件
├── ...
└── 书名_全文.txt          # 整本合订
```

## 重写某章

删掉对应章节文件和索引，重跑 `write` 即可从头开始：

```powershell
del data\novels\书名\chapter_001.txt
del data\novels\书名\chapters.json
del data\novels\书名\consistency.json
python main.py write
```

经验库不受影响——相同技法会自动去重，不会重复计数。

## API 配置

默认 DeepSeek，也支持其他后端：

| 后端 | 环境变量 | 备注 |
|------|----------|------|
| DeepSeek | `DEEPSEEK_API_KEY` | 默认 |
| OpenAI | `OPENAI_API_KEY` | 可选 `OPENAI_BASE_URL` |
| Claude | `ANTHROPIC_API_KEY` | 模型名含 "claude" |
| 中转 API | `OPENAI_API_KEY` | 必设 `OPENAI_BASE_URL` |

```powershell
$env:ARCHITECT_MODEL = "模型名"   # 各 Agent 可独立指定
$env:WRITER_MODEL    = "模型名"
$env:CRITIC_MODEL    = "模型名"
$env:REVISER_MODEL   = "模型名"
```

## 故障排查

**认证失败**：先确认 Key 已加载 `python -c "import os; print(os.getenv('DEEPSEEK_API_KEY')[:15])"`，空则用 `$env:XXX = "..."` 不能 `set`。再用 `python check_api.py` 自动测试。

**模型下载慢**：已配 HF 镜像，仍慢则 `$env:HF_ENDPOINT = "https://hf-mirror.com"`。

**JSON 解析失败**：系统会自动修复尾部逗号和截断，如仍失败会打印具体错误。通常调大对应 Agent 的 `max_tokens` 即可。

## License

MIT
