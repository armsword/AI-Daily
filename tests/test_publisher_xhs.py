import pytest
from unittest.mock import AsyncMock
from app.publisher.xiaohongshu import XhsPublisher


class TestXhsPublisher:
    def test_init_sets_cookie(self):
        publisher = XhsPublisher(cookie="test_cookie")
        assert publisher.cookie == "test_cookie"

    def test_parse_cookies(self):
        publisher = XhsPublisher(cookie="a1=abc; webId=123; gid=xyz")
        cookies = publisher._parse_cookies()
        assert len(cookies) == 3
        assert cookies[0] == {
            "name": "a1", "value": "abc",
            "domain": ".xiaohongshu.com", "path": "/",
        }
        assert cookies[1]["name"] == "webId"
        assert cookies[2]["value"] == "xyz"

    @pytest.mark.asyncio
    async def test_publish_draft_returns_false_on_empty_path(self):
        publisher = XhsPublisher(cookie="test_cookie")
        result = await publisher.publish_draft(
            image_path="", title="AI日报", description="测试"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_draft_calls_upload(self):
        publisher = XhsPublisher(cookie="a1=abc; webId=123")
        publisher._upload_via_browser = AsyncMock()

        result = await publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-08",
            description="今日AI趋势总结",
        )

        assert result is True
        publisher._upload_via_browser.assert_called_once_with(
            "/tmp/test.png", "AI日报 2026-05-08", "今日AI趋势总结"
        )

    @pytest.mark.asyncio
    async def test_publish_draft_returns_false_on_error(self):
        publisher = XhsPublisher(cookie="test_cookie")
        publisher._upload_via_browser = AsyncMock(
            side_effect=Exception("Browser failed")
        )

        result = await publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-08",
            description="测试",
        )

        assert result is False
