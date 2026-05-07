# Reddit 爬虫原理文档

## 概述

RedditCrawler 通过 Reddit 的公开 JSON API 抓取指定 subreddit 的最新帖子，并按关键词和时间窗口进行过滤。

## 核心原理

### 1. Reddit JSON API

Reddit 的每个页面 URL 后面加上 `.json` 即可获得 JSON 格式的数据。例如：

```
https://www.reddit.com/r/artificial/new.json?limit=50
```

返回结构：
```json
{
  "data": {
    "children": [
      {
        "data": {
          "title": "帖子标题",
          "url": "链接",
          "score": 分数,
          "created_utc": Unix时间戳,
          "selftext": "帖子正文",
          "permalink": "Reddit内部链接"
        }
      }
    ]
  }
}
```

### 2. 请求头要求

Reddit API 要求设置 `User-Agent` 头，否则可能返回 429（请求过多）。我们使用：

```python
headers = {"User-Agent": "AI-Daily-Bot/1.0"}
```

### 3. 数据流

```
初始化(subreddits, keywords, max_items)
        |
        v
crawl() 遍历每个 subreddit
        |
        v
fetch_subreddit() -> 请求 JSON API -> 解析为 NewsItem 列表
        |
        v
过滤：_is_within_24h() AND _matches_keywords()
        |
        v
返回过滤后的 NewsItem 列表
```

### 4. 过滤逻辑

- **时间过滤**：只保留 24 小时内发布的帖子（基于 `created_utc`）
- **关键词过滤**：帖子标题中包含任一关键词（大小写不敏感）

### 5. 错误处理

单个 subreddit 抓取失败不影响其他 subreddit，异常会被捕获并跳过。

## 类结构

```python
class RedditCrawler(BaseCrawler):
    def __init__(self, subreddits, keywords, max_items=50)
    async def fetch_subreddit(subreddit) -> list[NewsItem]
    def _matches_keywords(title) -> bool
    def _is_within_24h(published_at) -> bool
    async def crawl() -> list[NewsItem]  # 实现 BaseCrawler 抽象方法
```

## 依赖

- `httpx`：异步 HTTP 客户端
- `respx`：测试中用于 mock HTTP 请求
