# 定时调度模块原理文档

## 概述

定时调度模块是 AI-Daily 系统的核心编排层，负责按照配置的 cron 表达式定时触发日报生成流水线，将爬虫、分析、渲染、存储四个阶段串联为完整的自动化流程。

## 核心组件

### 1. APScheduler 调度器

使用 `apscheduler` 库的 `AsyncIOScheduler`，基于 asyncio 事件循环运行定时任务。

**选择原因：**
- 原生支持 asyncio，与项目中的异步爬虫、异步 LLM 调用无缝集成
- 支持标准 cron 表达式，配置灵活
- 轻量级，无需外部依赖（如 Celery + Redis）

### 2. CronTrigger

将 `config.yaml` 中的 `schedule.cron` 字段（如 `"0 8 * * *"` 表示每天早上8点）解析为 APScheduler 的 CronTrigger 对象。

```python
cron_parts = config.schedule.cron.split()  # ["0", "8", "*", "*", "*"]
trigger = CronTrigger(
    minute=cron_parts[0],    # 分
    hour=cron_parts[1],      # 时
    day=cron_parts[2],       # 日
    month=cron_parts[3],     # 月
    day_of_week=cron_parts[4],  # 星期
)
```

## 日报生成流水线 (run_daily_pipeline)

流水线按顺序执行以下四个阶段：

### 阶段 1: 新闻爬取

并行调用两个爬虫源：
- **HackerNewsCrawler**: 从 Hacker News API 抓取热门技术新闻
- **RedditCrawler**: 从 Reddit 指定子版块抓取相关帖子

爬取完成后进行 **URL 去重**，避免同一新闻出现在多个来源时重复处理。

```python
seen_urls = set()
unique_news = []
for item in all_news:
    if item.url not in seen_urls:
        seen_urls.add(item.url)
        unique_news.append(item)
```

### 阶段 2: LLM 分析

将去重后的新闻列表传给 `LLMAnalyzer`，由大语言模型进行：
- 新闻分类（按技术领域）
- 趋势总结
- 重要性排序（取 top_n 条）

### 阶段 3: 卡片渲染

将分析结果传给 `CardRenderer`，生成当日的可视化信息卡片（PNG 图片）。

### 阶段 4: 报告持久化

构建 `DailyReport` 对象并通过 `save_report` 写入 SQLite 数据库，包含：
- 日期
- 新闻条目列表
- 趋势总结文本
- 生成的图片路径

## 数据流图

```
config.yaml
    │
    ▼
┌─────────────────┐
│  create_daily_job│ ──► APScheduler (cron trigger)
└─────────────────┘
         │ 触发
         ▼
┌─────────────────────────────────────┐
│       run_daily_pipeline            │
│                                     │
│  HackerNewsCrawler ──┐              │
│                      ├─► 去重 ─► LLMAnalyzer ─► CardRenderer ─► save_report
│  RedditCrawler ──────┘              │
└─────────────────────────────────────┘
```

## 错误处理

当前版本采用 fail-fast 策略：任一阶段抛出异常，整个流水线中止并通过 logger 记录错误。APScheduler 默认会在下一个 cron 周期重新触发任务。

## 配置项

| 配置路径 | 说明 | 示例 |
|---------|------|------|
| `schedule.cron` | 定时触发表达式 | `"0 8 * * *"` |
| `crawler.keywords` | 爬虫过滤关键词 | `["AI", "LLM"]` |
| `crawler.max_items_per_source` | 每源最大条目数 | `30` |
| `llm.model` | 分析用模型 | `"gpt-4o-mini"` |
| `output.top_n` | 最终展示条数 | `15` |
| `output.dir` | 图片输出目录 | `"output"` |
| `output.card_width` | 卡片宽度(px) | `800` |
