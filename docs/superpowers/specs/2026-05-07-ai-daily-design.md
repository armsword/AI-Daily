# AI 日报服务设计文档

## 概述

一个自动化 AI 日报 Web 服务，每天定时从 Hacker News 和 Reddit 收集最近 24 小时的 AI 相关新闻，通过 LLM 进行深度分析（摘要、分类、趋势点评），生成精美的日报卡片长图，并通过简洁的单页 Web 界面展示。

## 技术栈

- **Web 框架：** FastAPI + Uvicorn
- **定时调度：** APScheduler（CronTrigger）
- **爬虫：** httpx（异步）
- **LLM：** litellm（统一接口，支持 Claude/OpenAI 等模型切换）
- **卡片渲染：** Jinja2 HTML 模板 + html2image（HTML→PNG）
- **数据存储：** SQLite（元数据）+ 本地文件系统（图片）
- **测试：** pytest + pytest-asyncio + respx

## 架构

```
┌─────────────────────────────────────────────┐
│                  FastAPI Web                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ 展示页面  │  │ API接口   │  │ 静态文件   │ │
│  └──────────┘  └──────────┘  └───────────┘ │
└─────────────────────────────────────────────┘
         ↑                          ↑
         │                          │
┌────────┴────────┐    ┌───────────┴──────────┐
│  APScheduler    │    │   生成的日报卡片图片    │
│  (每天定时触发)  │    │   (存储在本地文件系统)  │
└────────┬────────┘    └──────────────────────┘
         │                          ↑
         ▼                          │
┌─────────────────┐    ┌───────────┴──────────┐
│   新闻爬取模块   │───→│   内容分析 (LLM)      │
│  HN / Reddit    │    │   摘要+分类+点评       │
└─────────────────┘    └───────────┬──────────┘
                                   │
                                   ▼
                       ┌──────────────────────┐
                       │  卡片渲染 (HTML→图片)  │
                       │  html2image + 模板    │
                       └──────────────────────┘
```

**核心流程：** 定时触发 → 爬取新闻 → LLM 分析 → 渲染卡片图片 → Web 展示

## 模块设计

### 1. 新闻爬取模块

- **数据源：** Hacker News（官方 Firebase API）、Reddit（r/artificial, r/MachineLearning, r/LocalLLaMA）
- **爬取方式：** httpx 异步请求，HN 用官方 API，Reddit 用 JSON API（.json 后缀）
- **筛选逻辑：** 最近 24 小时内发布、AI 相关关键词过滤（AI, LLM, GPT, Claude, ML, deep learning 等）
- **去重：** 基于 URL 去重，避免跨平台重复
- **输出：** 统一的新闻列表结构（标题、链接、来源、发布时间、得分/热度、摘要）

### 2. LLM 分析模块

- **接口抽象：** 通过 litellm 统一调用，配置文件切换模型
- **处理流程：**
  1. 将爬取的新闻批量送给 LLM
  2. LLM 做：分类（大模型/应用/研究/开源/行业）、中文摘要、趋势点评
  3. 选出当日 Top 10-15 条最有价值的新闻
  4. 生成一段「今日 AI 趋势总结」（3-5 句话）

### 3. 卡片渲染模块

- **技术：** Jinja2 HTML 模板 + CSS 样式 → html2image 截图生成 PNG
- **卡片内容：** 日期标题、趋势总结、分类新闻列表（标题+一句话摘要+来源标签）
- **样式：** 深色/浅色主题，宽度固定 800px，长度自适应内容

### 4. Web 展示

- **单页设计：** 顶部展示最新一期日报卡片图，下方为历史日报列表（缩略图+日期）
- **静态文件服务：** FastAPI 直接 serve 生成的图片
- **数据存储：** SQLite 存储每日新闻元数据和生成记录，图片存本地 output/ 目录

### 5. 定时调度

- **APScheduler CronTrigger：** 每天早上 8:00 执行
- **配置化：** cron 表达式可在配置文件中修改

## 项目结构

```
ai-daily/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口 + APScheduler 启动
│   ├── config.py            # 配置管理
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── base.py          # 爬虫基类
│   │   ├── hackernews.py    # HN 爬虫
│   │   └── reddit.py        # Reddit 爬虫
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── llm_analyzer.py  # LLM 分析（litellm 统一接口）
│   ├── renderer/
│   │   ├── __init__.py
│   │   ├── card_renderer.py # 卡片生成逻辑
│   │   └── templates/
│   │       └── daily_card.html  # Jinja2 卡片模板
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── jobs.py          # 定时任务定义
│   ├── models.py            # SQLite 数据模型
│   └── static/              # CSS/字体等静态资源
├── output/                  # 生成的日报图片
├── templates/
│   └── index.html           # Web 展示页面
├── config.yaml              # 配置文件
├── requirements.txt
├── tests/
│   └── ...
└── docs/
```

## 配置文件 (config.yaml)

```yaml
# 定时任务
schedule:
  cron: "0 8 * * *"

# LLM 配置
llm:
  model: "claude-sonnet-4-20250514"
  api_key_env: "ANTHROPIC_API_KEY"

# 爬虫配置
crawler:
  sources:
    - hackernews
    - reddit
  reddit_subreddits:
    - artificial
    - MachineLearning
    - LocalLLaMA
  keywords:
    - AI
    - LLM
    - GPT
    - Claude
    - machine learning
    - deep learning
  max_items_per_source: 50

# 输出配置
output:
  dir: "output"
  card_width: 800
  top_n: 12
```

## 错误处理

- **爬虫容错：** 单个源失败不影响整体流程，记录错误日志继续处理其他源
- **LLM 调用失败：** 重试 2 次，仍失败则使用原始标题+摘要直接生成卡片（降级方案）
- **图片生成失败：** 记录错误，Web 页面展示「生成中」占位状态
- **日志：** 使用 Python logging，记录每次任务执行的关键节点和耗时

## 测试策略（TDD）

1. **爬虫模块测试：** Mock HTTP 响应，验证解析逻辑（HN API 格式、Reddit JSON 格式）
2. **分析模块测试：** Mock LLM 返回，验证分类/摘要/排序逻辑
3. **渲染模块测试：** 验证 HTML 模板渲染输出正确，图片文件生成成功
4. **调度模块测试：** 验证任务注册和触发逻辑
5. **API 测试：** FastAPI TestClient 验证接口响应

测试框架：pytest + pytest-asyncio + respx（mock httpx）

## 关键依赖

- `fastapi` + `uvicorn` — Web 服务
- `httpx` — 异步 HTTP 请求
- `apscheduler` — 定时调度
- `litellm` — LLM 统一接口
- `jinja2` — HTML 模板
- `html2image` — HTML 转图片
- `pydantic` — 数据模型验证
- `pyyaml` — 配置文件解析
- `pytest` + `pytest-asyncio` + `respx` — 测试
