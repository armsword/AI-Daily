import logging
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import feedparser
import httpx
from app.crawler.base import BaseCrawler
from app.models import NewsItem

logger = logging.getLogger(__name__)

TC_AI_FEED = "https://techcrunch.com/category/artificial-intelligence/feed/"


class TechCrunchCrawler(BaseCrawler):
    def __init__(self, max_items: int = 50):
        self.max_items = max_items

    def _is_within_24h(self, published_at: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return (now - published_at) < timedelta(hours=24)

    async def crawl(self) -> list[NewsItem]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(TC_AI_FEED)
                resp.raise_for_status()
                content = resp.text

            feed = feedparser.parse(content)
            items = []
            for entry in feed.entries[:self.max_items]:
                try:
                    published_at = parsedate_to_datetime(entry.get("published", ""))
                    if not published_at.tzinfo:
                        published_at = published_at.replace(tzinfo=timezone.utc)
                except Exception:
                    continue

                if not self._is_within_24h(published_at):
                    continue

                items.append(NewsItem(
                    title=entry.get("title", ""),
                    url=entry.get("link", ""),
                    source="techcrunch",
                    published_at=published_at,
                    score=0,
                    summary=entry.get("summary", "")[:200],
                ))
            return items
        except Exception as e:
            logger.error(f"TechCrunch crawl failed: {e}")
            return []
