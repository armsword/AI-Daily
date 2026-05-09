import httpx
from datetime import datetime, timezone, timedelta
from app.crawler.base import BaseCrawler
from app.models import NewsItem

HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class HackerNewsCrawler(BaseCrawler):
    def __init__(self, keywords: list[str], max_items: int = 50):
        self.keywords = [k.lower() for k in keywords]
        self.max_items = max_items

    async def fetch_top_story_ids(self) -> list[int]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{HN_API_BASE}/newstories.json")
            resp.raise_for_status()
            return resp.json()[:self.max_items]

    async def fetch_story(self, story_id: int) -> NewsItem | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{HN_API_BASE}/item/{story_id}.json")
            resp.raise_for_status()
            data = resp.json()

        if not data or data.get("type") != "story" or not data.get("url"):
            return None

        published_at = datetime.fromtimestamp(data["time"], tz=timezone.utc)
        return NewsItem(
            title=data.get("title", ""),
            url=data.get("url", ""),
            source="hackernews",
            published_at=published_at,
            score=data.get("score", 0),
            summary="",
        )

    def _matches_keywords(self, title: str) -> bool:
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.keywords)

    def _is_within_24h(self, published_at: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return (now - published_at) < timedelta(hours=24)

    async def crawl(self) -> list[NewsItem]:
        story_ids = await self.fetch_top_story_ids()
        items = []
        for story_id in story_ids:
            try:
                item = await self.fetch_story(story_id)
                if item is None:
                    continue
                if not self._is_within_24h(item.published_at):
                    continue
                if not self._matches_keywords(item.title):
                    continue
                items.append(item)
            except Exception:
                continue
        return items
