import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

CHANNELS_CREATE_URL = "https://channels.weixin.qq.com/platform/post/create"
DEFAULT_BGM = "宫崎骏的春天"


class WeixinChannelsPublisher:
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
                    "domain": ".qq.com",
                    "path": "/",
                })
        return cookies

    async def _upload_via_browser(self, image_path: str, title: str, description: str) -> None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            await context.add_cookies(self._parse_cookies())
            page = await context.new_page()

            await page.goto(CHANNELS_CREATE_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)

            # 切换到"图文"发布模式（如有 tab）
            await page.evaluate('''() => {
                const tabs = document.querySelectorAll('span, div, a');
                for (const tab of tabs) {
                    const text = tab.textContent.trim();
                    if (text === '图文' || text.includes('图文')) {
                        tab.click();
                        break;
                    }
                }
            }''')
            await page.wait_for_timeout(3000)

            # 上传图片
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(image_path)
            await page.wait_for_timeout(5000)

            # 填写标题
            title_input = page.locator('input[type="text"]').first
            if await title_input.count() > 0:
                await title_input.click()
                await title_input.fill(title)
            await page.wait_for_timeout(1000)

            # 填写正文
            editor = page.locator('[contenteditable="true"]').first
            if await editor.count() > 0:
                await editor.click()
                await page.wait_for_timeout(500)
                for line in description.split("\n"):
                    if line:
                        await page.keyboard.type(line, delay=10)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(100)

            await page.wait_for_timeout(2000)

            # 选择背景音乐
            if self.bgm:
                await self._select_bgm(page)

            await page.wait_for_timeout(2000)

            # 点击"发表"按钮
            await page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                for (const btn of buttons) {
                    const text = btn.textContent.trim();
                    if (text === '发表' || text === '发布') {
                        btn.click();
                        return;
                    }
                }
            }''')
            await page.wait_for_timeout(5000)

            await browser.close()

    async def _select_bgm(self, page) -> None:
        """搜索并选择背景音乐"""
        try:
            # 点击"选择音乐"或"添加音乐"
            await page.evaluate('''() => {
                const els = document.querySelectorAll('span, div, a, button');
                for (const el of els) {
                    const text = el.textContent.trim();
                    if (text.includes('选择音乐') || text.includes('添加音乐') || text.includes('配乐')) {
                        el.click();
                        return;
                    }
                }
            }''')
            await page.wait_for_timeout(3000)

            # 搜索音乐
            search_input = page.locator('input[placeholder*="搜索"], input[placeholder*="音乐"]').first
            if await search_input.count() > 0:
                await search_input.click()
                await search_input.fill(self.bgm)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)

                # 点击第一个搜索结果的"使用"按钮
                await page.evaluate('''() => {
                    const btns = document.querySelectorAll('span, button, div');
                    for (const btn of btns) {
                        const text = btn.textContent.trim();
                        if (text === '使用' || text === '选择' || text === '添加') {
                            btn.click();
                            return;
                        }
                    }
                }''')
                await page.wait_for_timeout(2000)
                logger.info(f"视频号背景音乐已选择: {self.bgm}")
            else:
                logger.warning("视频号未找到音乐搜索框")
        except Exception as e:
            logger.warning(f"视频号选择背景音乐失败（不影响发布）: {e}")

    async def publish_draft(self, image_path: str, title: str, description: str) -> bool:
        if not image_path:
            return False

        try:
            await self._upload_via_browser(image_path, title, description)
            logger.info(f"视频号发布成功: {title}")
            return True
        except Exception as e:
            logger.error(f"视频号发布失败: {e}")
            return False
