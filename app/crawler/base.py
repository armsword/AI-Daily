from abc import ABC, abstractmethod
from app.models import NewsItem


class BaseCrawler(ABC):
    @abstractmethod
    async def crawl(self) -> list[NewsItem]:
        pass
