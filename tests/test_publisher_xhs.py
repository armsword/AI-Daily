import pytest
from unittest.mock import patch, MagicMock
from app.publisher.xiaohongshu import XhsPublisher


class TestXhsPublisher:
    def test_init_sets_cookie(self):
        publisher = XhsPublisher(cookie="test_cookie")
        assert publisher.cookie == "test_cookie"

    @patch("app.publisher.xiaohongshu.XhsClient")
    def test_publish_draft_calls_create_image_note(self, mock_xhs_class):
        mock_client = MagicMock()
        mock_xhs_class.return_value = mock_client

        publisher = XhsPublisher(cookie="test_cookie")
        result = publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-08",
            description="今日AI趋势总结",
        )

        assert result is True
        mock_xhs_class.assert_called_once_with(cookie="test_cookie")
        mock_client.create_image_note.assert_called_once_with(
            title="AI日报 2026-05-08",
            desc="今日AI趋势总结",
            files=["/tmp/test.png"],
            is_private=True,
        )

    @patch("app.publisher.xiaohongshu.XhsClient")
    def test_publish_draft_returns_false_on_error(self, mock_xhs_class):
        mock_client = MagicMock()
        mock_client.create_image_note.side_effect = Exception("API error")
        mock_xhs_class.return_value = mock_client

        publisher = XhsPublisher(cookie="test_cookie")
        result = publisher.publish_draft(
            image_path="/tmp/test.png",
            title="AI日报 2026-05-08",
            description="今日AI趋势总结",
        )

        assert result is False

    @patch("app.publisher.xiaohongshu.XhsClient")
    def test_publish_draft_with_empty_image_path(self, mock_xhs_class):
        publisher = XhsPublisher(cookie="test_cookie")
        result = publisher.publish_draft(
            image_path="",
            title="AI日报 2026-05-08",
            description="测试",
        )

        assert result is False
        mock_xhs_class.return_value.create_image_note.assert_not_called()
