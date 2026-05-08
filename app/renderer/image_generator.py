import logging
from pathlib import Path
import httpx
from app.analyzer.llm_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

DAILY_PROMPT_TEMPLATE = """生成一张中文AI科技日报长图，严格参照以下风格和排版要求：

【重要】所有文字必须水平书写，每行文字严格保持水平平行，不要倾斜。

【整体风格】
- 手写钢笔/马克笔字体风格，中文手写体，温暖亲切
- 泛黄牛皮纸背景，带轻微褶皱和纸张纹理
- 所有文字必须使用中文（仅公司/产品专有名词保留英文，如OpenAI、GPT等）
- 竖版长图，宽窄比约3:5

【顶部区域】
- 左上角小字：「每天3分钟，掌握AI大事」
- 正中大标题：「AI日报」，使用粗体手写字，深棕色
- 标题下方：日期 {date}
- 右上角：用☑勾选框样式列出今日3个核心要点（简短中文）

【今日概要】
用一行带方框的小字简述：「{summary}」

【新闻正文】
按以下新闻逐条排列，每条新闻包含：
- 彩色圆角分类标签（橙色/蓝色/绿色/紫色，如「融资并购」「大模型」「开源」「研究」「行业应用」）
- 大号数字编号（①②③...）
- 中文粗体标题
- 2-3行中文说明文字
- 右侧或旁边配一个相关的手绘小插图/logo简笔画
- 条目之间用手绘虚线分隔

新闻内容：
{news_content}

【底部】
- 署名「AI日报 · 每日AI新闻速递」（仅此一行，不要再写其他总结文字）

【装饰元素】
- 适当添加手绘小图标：灯泡💡、火箭🚀、芯片、机器人等
- 用彩色马克笔高亮关键词
- 添加手绘箭头、星号、下划线等装饰
- 整体排版紧凑但不拥挤，留有适当留白"""


class NanoBananaImageGenerator:
    def __init__(self, api_key: str, api_base: str = "https://visionary.beer"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")

    def _build_prompt(self, date: str, analysis: AnalysisResult) -> str:
        circled_nums = "①②③④⑤⑥⑦⑧"
        news_lines = []
        for i, item in enumerate(analysis.categorized_news[:6], 0):
            summary = item.get("summary", "")
            category = item.get("category", "")
            num = circled_nums[i] if i < len(circled_nums) else str(i + 1)
            news_lines.append(f"{num}「{category}」{summary}")

        news_content = "\n\n".join(news_lines)
        summary = analysis.trend_summary[:40]
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
