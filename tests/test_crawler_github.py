import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from app.crawler.github_trending import GitHubTrendingCrawler


SAMPLE_RESPONSE = {
    "items": [
        {
            "full_name": "openai/whisper",
            "html_url": "https://github.com/openai/whisper",
            "description": "Robust Speech Recognition via Large-Scale Weak Supervision",
            "stargazers_count": 50000,
            "pushed_at": None,  # set dynamically
        },
        {
            "full_name": "old/repo",
            "html_url": "https://github.com/old/repo",
            "description": "Old repo",
            "stargazers_count": 100,
            "pushed_at": None,  # old
        },
    ]
}


@pytest.fixture
def crawler():
    return GitHubTrendingCrawler(token="", max_items=30)


@pytest.mark.asyncio
async def test_crawl_fetches_repos(crawler):
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=5)

    response_data = {
        "items": [
            {
                "full_name": "openai/whisper",
                "html_url": "https://github.com/openai/whisper",
                "description": "Speech Recognition",
                "stargazers_count": 50000,
                "pushed_at": recent.isoformat(),
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = lambda: None

    with patch("app.crawler.github_trending.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        items = await crawler.crawl()

    assert len(items) == 1
    assert items[0].title == "openai/whisper"
    assert items[0].source == "github"
    assert items[0].score == 50000
    assert items[0].summary == "Speech Recognition"


@pytest.mark.asyncio
async def test_crawl_returns_empty_on_error(crawler):
    with patch("app.crawler.github_trending.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("API error")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        items = await crawler.crawl()

    assert items == []
