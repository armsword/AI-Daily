# AI Daily - AI 日报自动化服务

每天定时从多个平台爬取 AI 相关新闻，通过 LLM 深度分析、分类、摘要，再调用 Nano Banana Pro 生成手绘风格的中文日报信息图，支持自动上传到社交平台草稿箱，最终通过 Web 页面展示。

![AI日报示例](docs/daily-example.jpg)

## 功能特性

- **多源新闻爬取**：自动抓取 Hacker News、Reddit、TechCrunch、Product Hunt、GitHub Trending 的 AI 新闻
- **智能去重**：URL 去重 + 标题相似度去重，避免连续多天内容重复
- **关键词过滤**：20+ 自定义关键词，精准筛选 AI 相关内容
- **LLM 智能分析**：使用大模型对新闻进行分类（大模型/应用/研究/开源/行业）、摘要和趋势总结
- **AI 信息图生成**：通过 Nano Banana Pro 生成手绘牛皮纸风格的中文日报长图
- **社交平台发布**：自动上传日报图片到小红书和抖音草稿箱（Playwright 浏览器自动化）
- **定时自动运行**：基于 APScheduler 定时执行（默认每天 10:30）
- **Web 页面展示**：简洁单页展示最新日报及历史记录，支持图片点击放大缩放

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 定时调度 | APScheduler (CronTrigger) |
| 新闻爬取 | httpx (async) + feedparser |
| LLM 分析 | litellm (支持多种模型) |
| 图片生成 | Nano Banana Pro (via Visionary API) |
| 社交发布 | Playwright (浏览器自动化) |
| 数据存储 | SQLite |
| 模板渲染 | Jinja2 |
| 测试 | pytest + pytest-asyncio + respx |

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export VISIONARY_API_KEY="your-visionary-api-key"

# 可选：社交平台自动发布
export XHS_COOKIE="your-xiaohongshu-cookie"
export DOUYIN_COOKIE="your-douyin-cookie"

# 可选：扩展采集源
export PRODUCTHUNT_TOKEN="your-producthunt-token"
export GITHUB_TOKEN="your-github-token"
```

- `ANTHROPIC_API_KEY`：用于 LLM 新闻分析
- `VISIONARY_API_KEY`：用于 Nano Banana Pro 图片生成（从 [visionary.beer](https://visionary.beer) 获取）
- `XHS_COOKIE`：小红书创作者平台 Cookie（从 creator.xiaohongshu.com 登录后获取）
- `DOUYIN_COOKIE`：抖音创作者中心 Cookie（从 creator.douyin.com 登录后获取）
- `PRODUCTHUNT_TOKEN`：Product Hunt API Token（可选，无则跳过该源）
- `GITHUB_TOKEN`：GitHub Token（可选，提高 API 请求频率）

### 3. 启动服务

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 查看日报页面。

### 4. 手动触发生成

```python
import asyncio
from app.config import load_config
from app.scheduler.jobs import run_daily_pipeline

asyncio.run(run_daily_pipeline(load_config("config.yaml")))
```

## 配置说明

编辑 `config.yaml` 自定义配置：

```yaml
schedule:
  cron: "30 10 * * *"          # 每天 10:30 自动执行

llm:
  model: "anthropic/auto"      # LLM 模型（通过 litellm 支持多种模型）

crawler:
  sources: [hackernews, reddit, techcrunch, producthunt, github]
  reddit_subreddits: [artificial, MachineLearning, LocalLLaMA]
  keywords: [AI, LLM, GPT, Claude, machine learning, deep learning, ...]
  max_items_per_source: 100

output:
  dir: "output"                # 图片输出目录
  top_n: 12                    # 筛选新闻条数
```

## 项目结构

```
AI-Daily/
├── app/
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 配置加载
│   ├── models.py              # 数据模型 + SQLite
│   ├── crawler/
│   │   ├── hackernews.py      # HN 爬虫
│   │   ├── reddit.py          # Reddit 爬虫
│   │   ├── techcrunch.py      # TechCrunch RSS 爬虫
│   │   ├── producthunt.py     # Product Hunt GraphQL 爬虫
│   │   └── github_trending.py # GitHub Trending 爬虫
│   ├── analyzer/
│   │   └── llm_analyzer.py    # LLM 分析
│   ├── renderer/
│   │   └── image_generator.py # Nano Banana Pro 图片生成
│   ├── publisher/
│   │   ├── xiaohongshu.py     # 小红书草稿发布
│   │   └── douyin.py          # 抖音草稿发布
│   └── scheduler/
│       └── jobs.py            # 定时任务 Pipeline
├── templates/
│   └── index.html             # Web 页面模板（支持图片缩放）
├── tests/                     # 测试用例
├── docs/                      # 设计文档
├── config.yaml                # 配置文件
└── requirements.txt           # 依赖
```

## Pipeline 流程

```
爬取新闻 (HN + Reddit + TechCrunch + Product Hunt + GitHub)
    ↓
关键词过滤 + URL去重 + 标题相似度去重
    ↓
LLM 分析 (分类/摘要/趋势总结)
    ↓
Nano Banana Pro 生成信息图
    ↓
保存报告 (SQLite) + 展示 (Web)
    ↓
自动上传草稿 (小红书 + 抖音)
```

## 运行测试

```bash
source .venv/bin/activate
pytest tests/ -v
```

## License

MIT
