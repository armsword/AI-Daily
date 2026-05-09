import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta
from app.crawler.techcrunch import TechCrunchCrawler

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item>
  <title>OpenAI launches new reasoning model</title>
  <link>https://techcrunch.com/2026/05/09/openai-reasoning/</link>
  <pubDate>{pub_date}</pubDate>
  <description>OpenAI announced a new reasoning model today.</description>
</item>
<item>
  <title>Old AI article from last week</title>
  <link>https://techcrunch.com/2026/05/01/old-article/</link>
  <pubDate>{old_date}</pubDate>
  <description>This is old news.</description>
</item>
</channel>
</rss>"""


@pytest.fixture
def crawler():
    return TechCrunchCrawler(max_items=50)


@pytest.fixture
def rss_feed():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(hours=2)
    old = now - timedelta(days=3)
    return SAMPLE_RSS.format(
        pub_date=recent.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        old_date=old.strftime("%a, %d %b %Y %H:%M:%S +0000"),
    )


@pytest.mark.asyncio
async def test_crawl_fetches_rss_and_filters_by_time(crawler, rss_feed):
    mock_response = AsyncMock()
    mock_response.text = rss_feed
    mock_response.raise_for_status = lambda: None

    with patch("app.crawler.techcrunch.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        items = await crawler.crawl()

    assert len(items) == 1
    assert items[0].title == "OpenAI launches new reasoning model"
    assert items[0].source == "techcrunch"
    assert items[0].url == "https://techcrunch.com/2026/05/09/openai-reasoning/"


@pytest.mark.asyncio
async def test_crawl_returns_empty_on_error(crawler):
    with patch("app.crawler.techcrunch.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client_class.return_value.__aenter__.return_value = mock_client

        items = await crawler.crawl()

    assert items == []
