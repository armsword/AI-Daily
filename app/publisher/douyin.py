import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

DOUYIN_CREATOR_URL = "https://creator.douyin.com/creator-micro/content/upload"


class DouyinPublisher:
    def __init__(self, cookie: str):
        self.cookie = cookie

    def _parse_cookies(self) -> list[dict]:
        cookies = []
        for item in self.cookie.split(";"):
            item = item.strip()
            if "=" in item:
                name, value = item.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".douyin.com",
                    "path": "/",
                })
        return cookies

    async def _upload_via_browser(self, image_path: str, title: str) -> None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.add_cookies(self._parse_cookies())
            page = await context.new_page()

            await page.goto(DOUYIN_CREATOR_URL, wait_until="networkidle")

            # 上传图片
            async with page.expect_file_chooser() as fc_info:
                await page.click('div[class*="upload"]')
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)

            # 等待上传完成
            await page.wait_for_timeout(3000)

            # 填写标题
            title_input = page.locator(
                'input[placeholder*="标题"], div[contenteditable="true"]'
            ).first
            await title_input.fill(title)

            # 点击保存草稿（不发布）
            draft_btn = page.locator(
                'button:has-text("存草稿"), button:has-text("保存草稿")'
            )
            if await draft_btn.count() > 0:
                await draft_btn.first.click()
                await page.wait_for_timeout(2000)

            await browser.close()

    async def publish_draft(self, image_path: str, title: str) -> bool:
        if not image_path:
            return False

        try:
            await self._upload_via_browser(image_path, title)
            logger.info(f"抖音草稿发布成功: {title}")
            return True
        except Exception as e:
            logger.error(f"抖音草稿发布失败: {e}")
            return False
