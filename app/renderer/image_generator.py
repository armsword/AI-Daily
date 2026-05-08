import logging
from pathlib import Path
import httpx
from app.analyzer.llm_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

DAILY_PROMPT_TEMPLATE = """生成一张中文AI科技日报信息图。

【排版核心规则——最高优先级】
- 想象画面中有一组等距的水平网格线，所有文字必须严格沿网格线水平书写，绝不倾斜
- 每行文字必须与上一行完全平行，行距保持一致
- 所有新闻条目占用相同高度，间距完全统一
- 分类标签统一出现在每条新闻左上方同一水平位置
- 编号数字统一在左侧同一垂直线上

【风格】
- 工整的中文手写印刷体，清晰易读，不要潦草
- 泛黄牛皮纸背景，温暖质感
- 竖版长图 3:5 比例
- 所有文字用中文（仅专有名词如OpenAI、GPT保留英文）

【布局】
顶部：左上「每天3分钟，掌握AI大事」| 居中大标题「AI日报」深棕色 | 日期 {date} | 右上☑核心要点
概要栏：方框内「{summary}」
正文：逐条排列，每条包含：彩色圆角分类标签 + 数字编号①②③ + 粗体中文标题 + 1-2行中文说明 + 右侧小插图，条目间虚线分隔
底部：「AI日报 · 每日AI新闻速递」

{news_content}

【装饰】少量手绘小图标点缀，不要喧宾夺主"""


class NanoBananaImageGenerator:
    def __init__(self, api_key: str, api_base: str = "https://visionary.beer"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")

    def _build_prompt(self, date: str, analysis: AnalysisResult) -> str:
        circled_nums = "①②③④⑤⑥⑦⑧"
        news_lines = []
        for i, item in enumerate(analysis.categorized_news[:6], 0):
            title = item.get("title", "")
            summary = item.get("summary", "")
            category = item.get("category", "")
            num = circled_nums[i] if i < len(circled_nums) else str(i + 1)
            news_lines.append(f"{num} 分类标签「{category}」\n标题：{title}\n说明：{summary}")

        news_content = "\n\n".join(news_lines)
        summary = analysis.trend_summary[:100]
        return DAILY_PROMPT_TEMPLATE.format(
            date=date, news_content=news_content, summary=summary
        )

    async def generate_daily_image(
        self, date: str, analysis: AnalysisResult, output_dir: str
    ) -> str:
        prompt = self._build_prompt(date, analysis)
        url = f"{self.api_base}/openapi/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "model": "Nano_Banana_Pro",
            "ratio": "9:16",
            "imageSize": "2K",
        }

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            image_url = data.get("results", [{}])[0].get("url", "")
            if not image_url:
                logger.warning("No image URL in Nano Banana Pro response")
                return ""

            # 下载图片
            async with httpx.AsyncClient(timeout=60.0) as client:
                img_resp = await client.get(image_url)
                img_resp.raise_for_status()
                image_bytes = img_resp.content

            Path(output_dir).mkdir(parents=True, exist_ok=True)
            filename = f"{date}.png"
            output_path = str(Path(output_dir) / filename)
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Daily image generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Nano Banana Pro image generation failed: {e}")
            return ""
