# Hacker News 爬虫原理文档

## 概述

HackerNews 爬虫模块通过 Hacker News 官方 Firebase API 获取热门故事，并根据关键词和时间窗口进行过滤，筛选出与 AI 相关的最新新闻。

## 架构设计

### 类继承结构

```
BaseCrawler (抽象基类)
└── HackerNewsCrawler (具体实现)
```

- `BaseCrawler`: 定义了 `crawl()` 抽象方法，所有爬虫必须实现该接口，返回 `list[NewsItem]`。
- `HackerNewsCrawler`: 具体实现，负责从 HN API 获取数据。

## API 原理

Hacker News 提供了基于 Firebase 的公开 REST API：

- **获取热门故事 ID 列表**: `GET https://hacker-news.firebaseio.com/v0/topstories.json`
  - 返回一个整数数组（故事 ID），按热度排序，最多 500 条
- **获取单条故事详情**: `GET https://hacker-news.firebaseio.com/v0/item/{id}.json`
  - 返回故事的完整信息：title, url, score, time, type 等

## 核心流程

```
1. fetch_top_story_ids()  →  获取前 N 个热门故事 ID（N = max_items）
2. 逐个调用 fetch_story(id) → 获取故事详情，转换为 NewsItem
3. 过滤逻辑:
   a. _is_within_24h()    →  只保留 24 小时内发布的故事
   b. _matches_keywords() →  标题中必须包含配置的关键词（大小写不敏感）
4. 返回过滤后的 NewsItem 列表
```

## 关键词匹配算法

采用简单的子字符串匹配：
- 将标题和关键词统一转为小写
- 检查标题中是否包含任意一个关键词
- 使用 `any()` 短路求值，匹配到第一个即返回 True

## 时间过滤

- HN API 返回的 `time` 字段是 Unix 时间戳（UTC）
- 转换为 `datetime` 对象后与当前 UTC 时间比较
- 差值超过 24 小时的故事被过滤掉

## 错误处理

- 单条故事获取失败时，跳过该条继续处理下一条（`try/except` + `continue`）
- 确保单个 API 请求失败不会导致整个爬取流程中断

## 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| keywords | 关键词列表，用于标题过滤 | 无（必填） |
| max_items | 最多获取的故事数量 | 50 |

## 依赖

- `httpx`: 异步 HTTP 客户端，支持 async/await
- `respx`: 测试中用于 mock HTTP 请求
