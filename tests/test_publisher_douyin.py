import pytest
from unittest.mock import patch, AsyncMock
from app.publisher.douyin import DouyinPublisher


class TestDouyinPublisher:
    def test_init_sets_cookie(self):
        publisher = DouyinPublisher(cookie="test_cookie")
        assert publisher.cookie == "test_cookie"

    def test_parse_cookies(self):
        publisher = DouyinPublisher(cookie="uid=123; sessionid=abc; token=xyz")
        cookies = publisher._parse_cookies()
        assert len(cookies) == 3
        assert cookies[0] == {
            "name": "uid", "value": "123",
            "domain": ".douyin.com", "path": "/",
        }
        assert cookies[1]["name"] == "sessionid"
        assert cookies[1]["value"] == "abc"

    @pytest.mark.asyncio
    async def test_publish_draft_returns_false_on_empty_path(self):
        publisher = DouyinPublisher(cookie="test_cookie")
        result = await publisher.publish_draft(image_path="", title="AI日报")
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_draft_calls_upload(self):
        publisher = DouyinPublisher(cookie="uid=123; sessionid=abc")
        publisher._upload_via_browser = AsyncMock()

        result = await publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-08",
        )

        assert result is True
        publisher._upload_via_browser.assert_called_once_with(
            "/tmp/test.png", "AI日报 2026-05-08"
        )

    @pytest.mark.asyncio
    async def test_publish_draft_returns_false_on_error(self):
        publisher = DouyinPublisher(cookie="test_cookie")
        publisher._upload_via_browser = AsyncMock(
            side_effect=Exception("Browser failed")
        )

        result = await publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-08",
        )

        assert result is False
