import logging
from datetime import datetime, timezone, timedelta
import httpx
from app.crawler.base import BaseCrawler
from app.models import NewsItem

logger = logging.getLogger(__name__)

PH_API_URL = "https://api.producthunt.com/v2/api/graphql"

PH_QUERY = """
query {
  posts(order: NEWEST, topic: "artificial-intelligence", first: %d) {
    edges {
      node {
        name
        tagline
        url
        votesCount
        createdAt
      }
    }
  }
}
"""


class ProductHuntCrawler(BaseCrawler):
    def __init__(self, token: str, max_items: int = 30):
        self.token = token
        self.max_items = max_items

    def _is_within_24h(self, published_at: datetime) -> bool:
        now = datetime.now(timezone.utc)
        return (now - published_at) < timedelta(hours=24)

    async def crawl(self) -> list[NewsItem]:
        if not self.token:
            return []

        try:
            query = PH_QUERY % self.max_items
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    PH_API_URL,
                    headers=headers,
                    json={"query": query},
                )
                resp.raise_for_status()
                data = resp.json()

            edges = data.get("data", {}).get("posts", {}).get("edges", [])
            items = []
            for edge in edges:
                node = edge.get("node", {})
                try:
                    created_at = datetime.fromisoformat(
                        node["createdAt"].replace("Z", "+00:00")
                    )
                except (KeyError, ValueError):
                    continue

                if not self._is_within_24h(created_at):
                    continue

                items.append(NewsItem(
                    title=node.get("name", ""),
                    url=node.get("url", ""),
                    source="producthunt",
                    published_at=created_at,
                    score=node.get("votesCount", 0),
                    summary=node.get("tagline", ""),
                ))
            return items
        except Exception as e:
            logger.error(f"Product Hunt crawl failed: {e}")
            return []
