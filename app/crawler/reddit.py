import httpx
from datetime import datetime, timezone, timedelta
from app.crawler.base import BaseCrawler
from app.models import NewsItem


class RedditCrawler(BaseCrawler):
    def __init__(self, subreddits: list[str], keywords: list[str], max_items: int = 50):
        self.subreddits = subreddits
        self.keywords = [k.lower() for k in keywords]
        self.max_items = max_items

    async def fetch_subreddit(self, subreddit: str) -> list[NewsItem]:
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        headers = {"User-Agent": "AI-Daily-Bot/1.0"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params={"limit": self.max_items})
            resp.raise_for_status()
            data = resp.json()

        items = []
        for child in data["data"]["children"]:
            post = child["data"]
            published_at = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
            item = NewsItem(
                title=post["title"],
                url=post["url"],
                source="reddit",
                published_at=published_at,
                score=post["score"],
                summary=post.get("selftext", "")[:200],
            )
            items.append(item)
        return items

    def _matches_keywords(self, title: str) -> bool:
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.keywords)

    def _is_within_24h(self, published_at: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return (now - published_at) < timedelta(hours=24)

    async def crawl(self) -> list[NewsItem]:
        all_items = []
        for subreddit in self.subreddits:
            try:
                posts = await self.fetch_subreddit(subreddit)
                all_items.extend(posts)
            except Exception:
                continue

        filtered = [
            item for item in all_items
            if self._is_within_24h(item.published_at) and self._matches_keywords(item.title)
        ]
        return filtered
