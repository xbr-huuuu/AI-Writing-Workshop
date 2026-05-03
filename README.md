<div align="center">

# 📚 AI 写作工坊

*用 DeepSeek 写长篇小说 · 大纲管理 · 连续写作 · 自动评分*

</div>

---

## 🚀 快速开始

### 1️⃣ 安装

```powershell
pip install -r requirements.txt
```

### 2️⃣ 配置 API Key

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的key"
```

```powershell
# 验证是否生效
python -c "import os; print('OK' if os.getenv('DEEPSEEK_API_KEY') else 'FAIL')"
```

> 永久生效：开始菜单搜「环境变量」→ 新建用户变量 → 变量名 `DEEPSEEK_API_KEY`，值填 Key。

### 3️⃣ 分析参考书籍（首次必做）

```powershell
python main.py analyze
```

系统逐本分析豆瓣经典书籍的写作特征，存入本地知识库。已分析过的自动跳过，可多次运行。跑完 20 本即可开始写作。

### 4️⃣ 创建小说

```powershell
python main.py init
```

按提示输入书名、类型、前提、章节数，自动生成完整大纲。

### 5️⃣ 开始写

```powershell
python main.py write      # 交互式写作
python main.py batch 5    # 连续写 5 章
python main.py rewrite    # 重写某章（优化文笔）
python main.py report     # 查看评分报告
python main.py outline    # 查看大纲
```

---

## 📋 命令一览

| 命令 | 说明 |
|------|------|
| `python main.py init` | 创建新小说 |
| `python main.py write` | 交互式写作，可选连续写几章 |
| `python main.py batch N` | 非交互连续写 N 章 |
| `python main.py outline` | 查看大纲 |
| `python main.py rewrite` | 重写某章（保留情节，优化文笔） |
| `python main.py report` | 写作评分报告 |
| `python main.py analyze` | 分析豆瓣书籍，可反复运行 |
| `python main.py stats` | 知识库数据量 |
| `python show_analysis.py` | 浏览已分析书籍 |
| `python show_analysis.py 书名` | 查看某本书分析详情 |
| `python check_api.py` | 诊断 API 连接 |

---

## 📁 项目结构

```
├── main.py              入口
├── config.py            配置 + 豆瓣书目
├── workflow.py          写作流程引擎
├── agents/              写作 Agent
├── knowledge_base/      书籍分析 & 文风提取
├── memory/              写作记忆 & 经验积累
└── data/                运行时数据（不提交 git）
    ├── vector_db/       向量知识库
    ├── novels/          你的书稿
    └── experience/      写作经验
```

### 📖 书稿位置

```
data/novels/书名/
├── outline.json          大纲
├── chapters.json         章节索引
├── chapter_001.txt       每章正文
├── chapter_002.txt
├── ...
└── 书名_全文.txt         整本合订
```

---

## 🔄 重写某一章

```powershell
del data\novels\书名\chapter_001.txt
del data\novels\书名\chapters.json
python main.py write
```

---

## ⚙️ 切换其他 API

支持 OpenAI、Claude 及第三方中转。

| 后端 | 环境变量 |
|------|----------|
| DeepSeek（默认） | `DEEPSEEK_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Claude | `ANTHROPIC_API_KEY` |
| 中转 API | `OPENAI_API_KEY` + `OPENAI_BASE_URL` |

```powershell
# 自定义模型名（可选）
$env:ARCHITECT_MODEL = "模型名"
$env:WRITER_MODEL    = "模型名"
$env:CRITIC_MODEL    = "模型名"
$env:REVISER_MODEL   = "模型名"
```

---

## 🛠 常见问题

<details>
<summary><b>认证失败</b></summary>

```powershell
# 1. 检查 Key 是否加载
python -c "import os; print(os.getenv('DEEPSEEK_API_KEY')[:15])"

# 2. 输出空 → 必须用 $env:XXX = "..." 不能 set

# 3. 自动诊断
python check_api.py
```
</details>

<details>
<summary><b>首次运行下载慢</b></summary>

已配置国内镜像，约 4 分钟。仍慢：

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```
</details>

<details>
<summary><b>章节内容被截断</b></summary>

在对应 Agent 文件中调大 `max_tokens` 参数。
</details>

---

<div align="center">

**MIT License**

</div>
