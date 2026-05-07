# LLM 分析模块原理文档

## 概述

LLM 分析模块负责将爬虫采集到的 AI 新闻列表发送给大语言模型进行智能分析，输出结构化的分析结果，包括趋势总结和分类新闻列表。

## 核心组件

### AnalysisResult (数据模型)

基于 Pydantic BaseModel，包含两个字段：

- `trend_summary: str` — 3-5 句话的今日 AI 趋势总结
- `categorized_news: list[dict]` — 分类后的新闻列表，每条包含 title/summary/category/source/url

### LLMAnalyzer (分析器)

初始化参数：
- `model: str` — LLM 模型名称（如 `claude-sonnet-4-20250514`）
- `top_n: int` — 最多返回的新闻条数，默认 12

## 工作流程

```
NewsItem 列表 → 格式化为文本 → 构造 Prompt → 调用 LLM API → 解析 JSON → AnalysisResult
```

### 1. 输入处理

将 `NewsItem` 列表转换为文本格式：
```
- [hackernews] GPT-5 Released (score: 500) URL: https://example.com/gpt5
- [reddit] New open source LLM (score: 300) URL: https://example.com/llm
```

### 2. Prompt 设计

Prompt 要求 LLM 完成四项任务：
1. 为每条新闻生成一句话中文摘要
2. 将新闻分类（大模型/应用/研究/开源/行业）
3. 按价值排序，选出最重要的新闻
4. 生成今日 AI 趋势总结

同时要求以严格 JSON 格式返回，便于程序解析。

### 3. LLM 调用

使用 `litellm` 库的 `acompletion` 异步接口：
- 支持多种 LLM 后端（OpenAI、Anthropic、Azure 等），通过 model 参数切换
- temperature 设为 0.3，保证输出稳定性
- 异步调用不阻塞事件循环

### 4. 结果解析

将 LLM 返回的 JSON 字符串解析为 Python dict，然后构造 `AnalysisResult` 对象。使用 `top_n` 截断新闻数量。

### 5. 容错机制

当 LLM 调用失败或返回格式异常时：
- 记录错误日志
- 返回 fallback 结果：trend_summary 为固定文案，categorized_news 使用原始标题作为摘要，分类标记为"未分类"

## 空列表处理

当输入为空列表时，直接返回空结果，不调用 LLM，避免浪费 API 资源。

## 依赖

- `litellm` — 统一的 LLM API 调用库，支持异步
- `pydantic` — 数据模型验证

## 使用示例

```python
from app.analyzer.llm_analyzer import LLMAnalyzer
from app.models import NewsItem

analyzer = LLMAnalyzer(model="claude-sonnet-4-20250514", top_n=12)
result = await analyzer.analyze(news_items)
print(result.trend_summary)
for news in result.categorized_news:
    print(f"[{news['category']}] {news['title']}: {news['summary']}")
```
