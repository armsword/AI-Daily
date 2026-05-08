import pytest
import httpx
import respx
from datetime import datetime, timezone
from app.crawler.hackernews import HackerNewsCrawler
from app.models import NewsItem


@pytest.fixture
def hn_crawler():
    return HackerNewsCrawler(keywords=["AI", "LLM", "GPT"], max_items=50)


@pytest.mark.asyncio
async def test_fetch_top_story_ids(hn_crawler):
    with respx.mock:
        respx.get("https://hacker-news.firebaseio.com/v0/topstories.json").mock(
            return_value=httpx.Response(200, json=[1, 2, 3, 4, 5])
        )
        ids = await hn_crawler.fetch_top_story_ids()
        assert ids == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_fetch_story_detail(hn_crawler):
    story_data = {
        "id": 123,
        "title": "New AI Model Released",
        "url": "https://example.com/ai",
        "score": 200,
        "time": int(datetime.now(timezone.utc).timestamp()) - 3600,
        "type": "story",
    }
    with respx.mock:
        respx.get("https://hacker-news.firebaseio.com/v0/item/123.json").mock(
            return_value=httpx.Response(200, json=story_data)
        )
        item = await hn_crawler.fetch_story(123)
        assert item is not None
        assert item.title == "New AI Model Released"
        assert item.source == "hackernews"


@pytest.mark.asyncio
async def test_filter_by_keywords(hn_crawler):
    story_ai = {
        "id": 1, "title": "New AI breakthrough", "url": "https://a.com",
        "score": 100, "time": int(datetime.now(timezone.utc).timestamp()) - 3600, "type": "story",
    }
    story_unrelated = {
        "id": 2, "title": "Cooking recipes", "url": "https://b.com",
        "score": 50, "time": int(datetime.now(timezone.utc).timestamp()) - 3600, "type": "story",
    }
    with respx.mock:
        respx.get("https://hacker-news.firebaseio.com/v0/topstories.json").mock(
            return_value=httpx.Response(200, json=[1, 2])
        )
        respx.get("https://hacker-news.firebaseio.com/v0/item/1.json").mock(
            return_value=httpx.Response(200, json=story_ai)
        )
        respx.get("https://hacker-news.firebaseio.com/v0/item/2.json").mock(
            return_value=httpx.Response(200, json=story_unrelated)
        )
        items = await hn_crawler.crawl()
        assert len(items) == 1
        assert items[0].title == "New AI breakthrough"


@pytest.mark.asyncio
async def test_filter_by_time_24h(hn_crawler):
    now = datetime.now(timezone.utc)
    old_time = int((now.timestamp()) - 90000)  # 25 hours ago
    story_old = {
        "id": 1, "title": "Old AI news", "url": "https://a.com",
        "score": 100, "time": old_time, "type": "story",
    }
    with respx.mock:
        respx.get("https://hacker-news.firebaseio.com/v0/topstories.json").mock(
            return_value=httpx.Response(200, json=[1])
        )
        respx.get("https://hacker-news.firebaseio.com/v0/item/1.json").mock(
            return_value=httpx.Response(200, json=story_old)
        )
        items = await hn_crawler.crawl()
        assert len(items) == 0
