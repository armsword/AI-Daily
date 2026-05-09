import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

DOUYIN_CREATOR_URL = "https://creator.douyin.com/creator-micro/content/upload"
DEFAULT_BGM = "宫崎骏的春天"


class DouyinPublisher:
    def __init__(self, cookie: str, bgm: str = DEFAULT_BGM):
        self.cookie = cookie
        self.bgm = bgm

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

            # 选择背景音乐
            if self.bgm:
                await self._select_bgm(page)

            # 点击保存草稿（不发布）
            draft_btn = page.locator(
                'button:has-text("存草稿"), button:has-text("保存草稿")'
            )
            if await draft_btn.count() > 0:
                await draft_btn.first.click()
                await page.wait_for_timeout(2000)

            await browser.close()

    async def _select_bgm(self, page) -> None:
        """搜索并选择背景音乐"""
        try:
            # 点击"选择音乐"
            await page.evaluate('''() => {
                const els = document.querySelectorAll('span, div, a');
                for (const el of els) {
                    const text = el.textContent.trim();
                    if (text === '选择音乐') {
                        el.click();
                        return;
                    }
                }
            }''')
            await page.wait_for_timeout(3000)

            # 搜索音乐
            search_input = page.locator('input[placeholder*="搜索"]').first
            if await search_input.count() > 0:
                await search_input.click()
                await search_input.fill(self.bgm)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)

                # 点击第一个结果的"使用"按钮
                await page.evaluate('''() => {
                    const btns = document.querySelectorAll('span, button, div');
                    for (const btn of btns) {
                        const text = btn.textContent.trim();
                        if (text === '使用' || text === '选择') {
                            btn.click();
                            return;
                        }
                    }
                }''')
                await page.wait_for_timeout(2000)
                logger.info(f"抖音背景音乐已选择: {self.bgm}")
            else:
                logger.warning("抖音未找到音乐搜索框")
        except Exception as e:
            logger.warning(f"抖音选择背景音乐失败（不影响发布）: {e}")

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
