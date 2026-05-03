# AI 写作工坊

> 多维度检索豆瓣 Top100 技法，多 Agent 协作，写完一章自动提炼技法。六套系统确保 30 章长篇小说前后联通、细节不丢、越写越好。

## 核心机制

### 跨章联通：写第 15 章时 AI 拿到什么

```
┌─ 第13-14章全文        → 细节不丢（对话、动作、场景）
├─ 第1-12章摘要          → 情节骨架不丢
├─ 实体注册表            → 人名/地名/物品名 + 状态变化不丢
├─ 一致性清单            → 埋了没收的伏笔不丢
├─ 上章批评意见          → 上一章犯的错不重复
└─ 多维度书目技法        → 开篇学A、高潮学B、结尾学C
```

### 实体注册表：存变不存不变

每章写完自动提取人物、地名、物品、组织，存入 `entity_registry.json`。只有状态变化才追加记录，不变不写。写新章时按名索引，AI 一眼看到每个实体的当前状态。

```json
{
  "林远舟": {
    "type": "人物",
    "state_history": [
      {"chapter": 1, "description": "理想主义天体语言学家"},
      {"chapter": 5, "description": "开始怀疑信号真实性"}
    ]
  },
  "徐方": {"type": "人物", "state_history": [{"chapter": 1, "description": "材料物理学家，断了一根手指"}]}
}
```

第一章有正文但没注册表时，系统自动回填。配角名字不会因为出现在第 3 章而在第 20 章被遗忘。

### 多维度检索：集百家之长

不同书擅长不同东西——《百年孤独》的开篇、《三体》的悬念、《雪国》的留白。系统按写作维度分别检索，去重后按用途标注：

| 维度 | 检索方向 | 可能搜到 |
|------|---------|---------|
| 开篇技法 | 悬念切入、场景描写 | 《百年孤独》《1984》 |
| 高潮设计 | 情节转折、情感峰值 | 《三体》《罪与罚》 |
| 结尾钩子 | 留白、反转 | 《雪国》《基地》 |
| 节奏控制 | 张弛、场景转换 | 《冰与火之歌》《沙丘》 |
| 语言描写 | 用词、意象、环境 | 《红楼梦》《边城》 |
| 对话人物 | 对话写作、心理描写 | 《围城》《活着》 |

### 技法提炼：写一章长一条

```
写完一章 → 自我反思 → 拆成独立技法卡片 → MD5 去重 → 存入经验库
         → 下章写作时自动检索已验证的高分技法
```

删了重写不会重复计数，相同技法只存一次。进化报告按技法分类纵向展示。

### 防崩机制

- **批评家反馈闭环**：上章扣分项直接喂给下章作家，"上章没对话，本章至少 3 段对话"
- **对话检测**：支持全角引号 `"..."`、方括号 `「」`、引导词 `说/道/问`，不再误报 0%
- **JSON 自动修复**：截断补全 + 尾部逗号修复，API 返回不完整也能抢救
- **API 三次重试**：指数退避（3s→6s→9s），网络抖动不丢进度
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
| `python main.py report` | 进化报告（技法分类+评分趋势） |
| `python main.py analyze` | 分析豆瓣 Top100 书籍 |
| `python main.py stats` | 知识库数据量 |
| `python show_analysis.py` | 浏览所有已分析书籍 |
| `python show_analysis.py 书名` | 查看某本书分析报告 |
| `python check_api.py` | 诊断 API 连接 |

## 项目结构

```
├── main.py                      ← 入口
├── config.py                    ← 配置 + 豆瓣 Top100 书目
├── workflow.py                  ← 核心引擎，串联全部系统
├── check_api.py                 ← API 诊断
├── show_analysis.py             ← 浏览书籍分析
├── requirements.txt
│
├── agents/
│   ├── architect.py             #   架构师：多维度检索 + 结构设计
│   ├── writer.py                #   作家：多维度检索 + 批评反馈 + 实体上下文
│   ├── critic.py                #   批评家：对标评审 + 一致性核验
│   ├── reviser.py               #   修订者：上限 3 条精准修改
│   └── llm_client.py            #   API 调用（自动重试）
│
├── knowledge_base/
│   ├── vector_store.py          #   ChromaDB 向量存储
│   ├── book_analyzer.py         #   豆瓣书籍分析
│   └── style_extractor.py       #   文风指纹 + 对话检测
│
├── memory/
│   ├── experience_log.py        #   技法提炼 + MD5 去重
│   ├── dynamic_fewshot.py       #   动态检索成功技法
│   ├── consistency_tracker.py   #   伏笔/角色一致性追踪
│   └── entity_tracker.py        #   实体注册表（人名/地名/物品）
│
└── data/                        ← 运行数据（不提交 git）
    ├── vector_db/               #   豆瓣分析 + 经验向量
    ├── novels/                  #   书稿
    └── experience/              #   技法卡片
```

## 书稿文件

```
data/novels/书名/
├── outline.json           # 全局大纲 + 硬软约束
├── chapters.json          # 章节索引（含摘要 + 评分）
├── consistency.json       # 伏笔/角色一致性追踪
├── entity_registry.json   # 实体注册表（人物/地点/物品状态变化）
├── chapter_001.txt        # 每章独立文件
├── ...
└── 书名_全文.txt          # 整本合订
```

## 重写某章

```powershell
del data\novels\书名\chapter_001.txt
del data\novels\书名\chapters.json
del data\novels\书名\consistency.json
del data\novels\书名\entity_registry.json
python main.py write
```

下次加载时会自动回填已有章节的实体。经验库不受影响。

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

**认证失败**：`python -c "import os; print(os.getenv('DEEPSEEK_API_KEY')[:15])"` 空则用 `$env:XXX = "..."` 不能 `set`。再用 `python check_api.py` 测试。

**模型下载慢**：已配 HF 镜像，仍慢则 `$env:HF_ENDPOINT = "https://hf-mirror.com"`。

**JSON 解析失败**：会自动修复尾部逗号和截断，仍失败会打印错误定位。通常调大对应 Agent 的 `max_tokens` 即可。

## License

MIT
