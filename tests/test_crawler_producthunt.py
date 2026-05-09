import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta
from app.crawler.producthunt import ProductHuntCrawler

SAMPLE_RESPONSE = {
    "data": {
        "posts": {
            "edges": [
                {
                    "node": {
                        "name": "AI Code Assistant",
                        "tagline": "Write code faster with AI",
                        "url": "https://www.producthunt.com/posts/ai-code-assistant",
                        "votesCount": 150,
                        "createdAt": None,  # will be set dynamically
                    }
                },
                {
                    "node": {
                        "name": "Old Product",
                        "tagline": "From last week",
                        "url": "https://www.producthunt.com/posts/old-product",
                        "votesCount": 50,
                        "createdAt": None,  # old date
                    }
                },
            ]
        }
    }
}


@pytest.fixture
def crawler():
    return ProductHuntCrawler(token="test-token", max_items=30)


@pytest.mark.asyncio
async def test_crawl_fetches_and_filters_by_time(crawler):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=2)).isoformat()
    old = (now - timedelta(days=3)).isoformat()

    response_data = {
        "data": {
            "posts": {
                "edges": [
                    {"node": {"name": "AI Code Assistant", "tagline": "Write code faster",
                              "url": "https://producthunt.com/posts/ai-code", "votesCount": 150,
                              "createdAt": recent}},
                    {"node": {"name": "Old Product", "tagline": "Old",
                              "url": "https://producthunt.com/posts/old", "votesCount": 50,
                              "createdAt": old}},
                ]
            }
        }
    }

    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = lambda: None

    with patch("app.crawler.producthunt.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        items = await crawler.crawl()

    assert len(items) == 1
    assert items[0].title == "AI Code Assistant"
    assert items[0].source == "producthunt"
    assert items[0].score == 150


@pytest.mark.asyncio
async def test_crawl_returns_empty_without_token():
    crawler = ProductHuntCrawler(token="", max_items=30)
    items = await crawler.crawl()
    assert items == []


@pytest.mark.asyncio
async def test_crawl_returns_empty_on_error(crawler):
    with patch("app.crawler.producthunt.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("API error")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        items = await crawler.crawl()

    assert items == []
