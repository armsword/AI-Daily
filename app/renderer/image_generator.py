import base64
import logging
from pathlib import Path
import httpx
from app.analyzer.llm_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

DAILY_PROMPT_TEMPLATE = """请生成一张中文AI日报信息图，手绘插画风格，暖色调牛皮纸背景。

要求：
- 顶部大标题「AI日报」，日期：{date}
- 右上角简短总结今日要点（2-3行小字）
- 正文按编号排列以下新闻，每条新闻配一个相关的小图标/插画：

{news_content}

风格要求：
- 手绘涂鸦风格，像笔记本上的手写笔记
- 牛皮纸/米黄色温暖背景
- 用不同颜色的标记笔标注重点
- 每条新闻有编号，标题加粗，下方小字是简短说明
- 适当添加箭头、圆圈、星号等手绘装饰元素
- 底部有一行小字「AI日报 · 每日AI新闻速递」
- 竖版排列，类似报纸版面
- 文字必须清晰可读"""


class MiniMaxImageGenerator:
    def __init__(self, api_key: str, api_base: str = "https://api.minimaxi.com"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")

    def _build_prompt(self, date: str, analysis: AnalysisResult) -> str:
        news_lines = []
        for i, item in enumerate(analysis.categorized_news[:8], 1):
            title = item.get("title", "")
            summary = item.get("summary", "")
            category = item.get("category", "")
            news_lines.append(f"{i}. 【{category}】{title}\n   {summary}")

        news_content = "\n\n".join(news_lines)
        return DAILY_PROMPT_TEMPLATE.format(date=date, news_content=news_content)

    async def generate_daily_image(
        self, date: str, analysis: AnalysisResult, output_dir: str
    ) -> str:
        prompt = self._build_prompt(date, analysis)
        url = f"{self.api_base}/v1/image_generation"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "image-01",
            "prompt": prompt,
            "aspect_ratio": "3:4",
            "response_format": "base64",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code", 0) != 0:
                raise ValueError(f"MiniMax API error: {base_resp.get('status_msg', 'unknown')}")

            image_b64 = data["data"]["image_base64"][0]
            image_bytes = base64.b64decode(image_b64)

            Path(output_dir).mkdir(parents=True, exist_ok=True)
            filename = f"{date}.png"
            output_path = str(Path(output_dir) / filename)
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Daily image generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"MiniMax image generation failed: {e}")
            return ""
