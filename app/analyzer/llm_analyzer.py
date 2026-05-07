import json
import logging
from pydantic import BaseModel
from litellm import acompletion
from app.models import NewsItem

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """你是一个AI新闻分析师。请分析以下AI相关新闻，完成以下任务：

1. 为每条新闻生成一句话中文摘要
2. 将新闻分类（大模型/应用/研究/开源/行业）
3. 按价值排序，选出最重要的新闻
4. 生成3-5句话的「今日AI趋势总结」

新闻列表：
{news_list}

请以如下JSON格式返回（不要包含markdown代码块标记）：
{{
  "trend_summary": "今日AI趋势总结...",
  "categorized_news": [
    {{"title": "原标题", "summary": "一句话中文摘要", "category": "分类", "source": "来源", "url": "链接"}}
  ]
}}"""


class AnalysisResult(BaseModel):
    trend_summary: str
    categorized_news: list[dict]


class LLMAnalyzer:
    def __init__(self, model: str, top_n: int = 12):
        self.model = model
        self.top_n = top_n

    async def analyze(self, news_items: list[NewsItem]) -> AnalysisResult:
        if not news_items:
            return AnalysisResult(trend_summary="", categorized_news=[])

        news_list = "\n".join(
            f"- [{item.source}] {item.title} (score: {item.score}) URL: {item.url}"
            for item in news_items
        )
        prompt = ANALYSIS_PROMPT.format(news_list=news_list)

        try:
            response = await acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            result = AnalysisResult(
                trend_summary=data["trend_summary"],
                categorized_news=data["categorized_news"][:self.top_n],
            )
            return result
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            fallback_news = [
                {"title": item.title, "summary": item.title, "category": "未分类", "source": item.source, "url": item.url}
                for item in news_items[:self.top_n]
            ]
            return AnalysisResult(trend_summary="AI新闻汇总", categorized_news=fallback_news)
