import pytest
from unittest.mock import AsyncMock
from app.publisher.weixin_channels import WeixinChannelsPublisher


class TestWeixinChannelsPublisher:
    def test_init_sets_cookie(self):
        publisher = WeixinChannelsPublisher(cookie="test_cookie")
        assert publisher.cookie == "test_cookie"

    def test_parse_cookies(self):
        publisher = WeixinChannelsPublisher(cookie="sid=abc; uid=123; token=xyz")
        cookies = publisher._parse_cookies()
        assert len(cookies) == 3
        assert cookies[0] == {
            "name": "sid", "value": "abc",
            "domain": ".qq.com", "path": "/",
        }
        assert cookies[1]["name"] == "uid"
        assert cookies[2]["value"] == "xyz"

    @pytest.mark.asyncio
    async def test_publish_draft_returns_false_on_empty_path(self):
        publisher = WeixinChannelsPublisher(cookie="test_cookie")
        result = await publisher.publish_draft(
            image_path="", title="AI日报", description="测试"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_draft_calls_upload(self):
        publisher = WeixinChannelsPublisher(cookie="sid=abc; uid=123")
        publisher._upload_via_browser = AsyncMock()

        result = await publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-09",
            description="今日AI趋势总结",
        )

        assert result is True
        publisher._upload_via_browser.assert_called_once_with(
            "/tmp/test.png", "AI日报 2026-05-09", "今日AI趋势总结"
        )

    @pytest.mark.asyncio
    async def test_publish_draft_returns_false_on_error(self):
        publisher = WeixinChannelsPublisher(cookie="test_cookie")
        publisher._upload_via_browser = AsyncMock(
            side_effect=Exception("Browser failed")
        )

        result = await publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-09",
            description="测试",
        )

        assert result is False
