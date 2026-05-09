import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?source=official"


class XhsPublisher:
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
                    "domain": ".xiaohongshu.com",
                    "path": "/",
                })
        return cookies

    async def _upload_via_browser(self, image_path: str, title: str, description: str) -> None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            await context.add_cookies(self._parse_cookies())
            page = await context.new_page()

            await page.goto(XHS_PUBLISH_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # 切换到"上传图文"标签
            await page.evaluate('''() => {
                const tabs = document.querySelectorAll('span.title');
                for (const tab of tabs) {
                    if (tab.textContent.includes('上传图文')) {
                        tab.click();
                        break;
                    }
                }
            }''')
            await page.wait_for_timeout(3000)

            # 上传图片
            file_input = page.locator('input[type="file"][accept*=".png"]')
            await file_input.set_input_files(image_path)
            await page.wait_for_timeout(5000)

            # 填写标题
            title_input = page.locator('input.c-input_inner')
            if await title_input.count() > 0:
                await title_input.first.fill(title)

            await page.wait_for_timeout(1000)

            # 点击"暂存离开"保存草稿
            await page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    if (btn.textContent.includes('暂存')) {
                        btn.click();
                        return;
                    }
                }
            }''')
            await page.wait_for_timeout(3000)

            await browser.close()

    async def publish_draft(self, image_path: str, title: str, description: str) -> bool:
        if not image_path:
            return False

        try:
            await self._upload_via_browser(image_path, title, description)
            logger.info(f"小红书草稿发布成功: {title}")
            return True
        except Exception as e:
            logger.error(f"小红书草稿发布失败: {e}")
            return False
