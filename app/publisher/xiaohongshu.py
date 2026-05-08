import logging
from xhs import XhsClient

logger = logging.getLogger(__name__)


class XhsPublisher:
    def __init__(self, cookie: str):
        self.cookie = cookie

    def publish_draft(self, image_path: str, title: str, description: str) -> bool:
        if not image_path:
            return False

        try:
            client = XhsClient(cookie=self.cookie)
            client.create_image_note(
                title=title,
                desc=description,
                files=[image_path],
                is_private=True,
            )
            logger.info(f"小红书草稿发布成功: {title}")
            return True
        except Exception as e:
            logger.error(f"小红书草稿发布失败: {e}")
            return False
