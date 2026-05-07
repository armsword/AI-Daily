import pytest
import httpx
import respx
from datetime import datetime, timezone
from app.crawler.reddit import RedditCrawler
from app.models import NewsItem


@pytest.fixture
def reddit_crawler():
    return RedditCrawler(
        subreddits=["artificial", "MachineLearning"],
        keywords=["AI", "LLM", "GPT"],
        max_items=50,
    )


@pytest.mark.asyncio
async def test_fetch_subreddit_posts(reddit_crawler):
    reddit_response = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "New LLM beats GPT-4",
                        "url": "https://example.com/llm",
                        "score": 500,
                        "created_utc": datetime(2026, 5, 7, 6, 0, 0, tzinfo=timezone.utc).timestamp(),
                        "selftext": "A new model...",
                        "permalink": "/r/artificial/comments/abc/new_llm/",
                    }
                }
            ]
        }
    }
    with respx.mock:
        respx.get("https://www.reddit.com/r/artificial/new.json").mock(
            return_value=httpx.Response(200, json=reddit_response)
        )
        posts = await reddit_crawler.fetch_subreddit("artificial")
        assert len(posts) == 1
        assert posts[0].title == "New LLM beats GPT-4"
        assert posts[0].source == "reddit"


@pytest.mark.asyncio
async def test_filter_by_keywords_reddit(reddit_crawler):
    reddit_response = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Cooking with Python",
                        "url": "https://example.com/cook",
                        "score": 100,
                        "created_utc": datetime(2026, 5, 7, 6, 0, 0, tzinfo=timezone.utc).timestamp(),
                        "selftext": "",
                        "permalink": "/r/artificial/comments/xyz/cook/",
                    }
                }
            ]
        }
    }
    with respx.mock:
        respx.get("https://www.reddit.com/r/artificial/new.json").mock(
            return_value=httpx.Response(200, json=reddit_response)
        )
        respx.get("https://www.reddit.com/r/MachineLearning/new.json").mock(
            return_value=httpx.Response(200, json={"data": {"children": []}})
        )
        items = await reddit_crawler.crawl()
        assert len(items) == 0


@pytest.mark.asyncio
async def test_crawl_multiple_subreddits(reddit_crawler):
    now_ts = datetime(2026, 5, 7, 6, 0, 0, tzinfo=timezone.utc).timestamp()
    response_artificial = {
        "data": {"children": [{"data": {
            "title": "AI breakthrough", "url": "https://a.com",
            "score": 200, "created_utc": now_ts, "selftext": "", "permalink": "/r/artificial/comments/a/ai/",
        }}]}
    }
    response_ml = {
        "data": {"children": [{"data": {
            "title": "GPT-5 paper", "url": "https://b.com",
            "score": 300, "created_utc": now_ts, "selftext": "", "permalink": "/r/MachineLearning/comments/b/gpt/",
        }}]}
    }
    with respx.mock:
        respx.get("https://www.reddit.com/r/artificial/new.json").mock(
            return_value=httpx.Response(200, json=response_artificial)
        )
        respx.get("https://www.reddit.com/r/MachineLearning/new.json").mock(
            return_value=httpx.Response(200, json=response_ml)
        )
        items = await reddit_crawler.crawl()
        assert len(items) == 2
