import logging
from datetime import datetime, timezone, timedelta, date
import httpx
from app.crawler.base import BaseCrawler
from app.models import NewsItem

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubTrendingCrawler(BaseCrawler):
    def __init__(self, token: str = "", max_items: int = 30):
        self.token = token
        self.max_items = max_items

    async def crawl(self) -> list[NewsItem]:
        try:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            query = f"topic:artificial-intelligence OR topic:llm OR topic:machine-learning pushed:>{yesterday}"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": self.max_items,
            }
            headers = {"Accept": "application/vnd.github+json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            async with httpx.AsyncClient() as client:
                resp = await client.get(GITHUB_SEARCH_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            items = []
            for repo in data.get("items", []):
                try:
                    pushed_at = datetime.fromisoformat(
                        repo["pushed_at"].replace("Z", "+00:00")
                    )
                except (KeyError, ValueError):
                    continue

                items.append(NewsItem(
                    title=repo.get("full_name", ""),
                    url=repo.get("html_url", ""),
                    source="github",
                    published_at=pushed_at,
                    score=repo.get("stargazers_count", 0),
                    summary=repo.get("description", "") or "",
                ))
            return items
        except Exception as e:
            logger.error(f"GitHub trending crawl failed: {e}")
            return []
