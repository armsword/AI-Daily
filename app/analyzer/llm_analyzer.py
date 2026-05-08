import json
import re
import logging
from pydantic import BaseModel
from litellm import acompletion
from app.models import NewsItem

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """你是AI新闻分析师。分析以下新闻，选出最重要的{top_n}条，返回纯JSON（不要markdown代码块）。

要求：
- summary: 20-25字中文摘要，必须是完整通顺的中文句子
- category: 只能是 大模型/应用/研究/开源/行业 之一
- trend_summary: 3句话总结今日趋势
- title和url保持原样不要修改

新闻列表：
{news_list}

返回格式（纯JSON，无其他文字）：
{{"trend_summary":"总结","categorized_news":[{{"title":"原标题","summary":"短摘要","category":"分类","source":"来源","url":"原url"}}]}}"""


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

        # 限制送入LLM的数量，避免输出过长导致JSON解析失败
        items_to_analyze = news_items[:30]
        news_list = "\n".join(
            f"- [{item.source}] {item.title} (score: {item.score}) URL: {item.url}"
            for item in items_to_analyze
        )
        prompt = ANALYSIS_PROMPT.format(news_list=news_list, top_n=self.top_n)

        try:
            response = await acompletion(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            # 提取 JSON：从第一个 { 到最后一个 }
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in LLM response")
            json_str = content[start:end]
            data = json.loads(json_str)
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
