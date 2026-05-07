import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone
from app.analyzer.llm_analyzer import LLMAnalyzer, AnalysisResult
from app.models import NewsItem


@pytest.fixture
def sample_news():
    return [
        NewsItem(
            title="GPT-5 Released",
            url="https://example.com/gpt5",
            source="hackernews",
            published_at=datetime(2026, 5, 7, 10, 0, 0, tzinfo=timezone.utc),
            score=500,
            summary="",
        ),
        NewsItem(
            title="New open source LLM",
            url="https://example.com/llm",
            source="reddit",
            published_at=datetime(2026, 5, 7, 8, 0, 0, tzinfo=timezone.utc),
            score=300,
            summary="",
        ),
    ]


@pytest.fixture
def analyzer():
    return LLMAnalyzer(model="claude-sonnet-4-20250514", top_n=12)


def test_analysis_result_structure():
    result = AnalysisResult(
        trend_summary="AI is advancing rapidly",
        categorized_news=[
            {"title": "GPT-5", "summary": "New model", "category": "大模型", "source": "hackernews", "url": "https://example.com"},
        ],
    )
    assert result.trend_summary == "AI is advancing rapidly"
    assert len(result.categorized_news) == 1


@pytest.mark.asyncio
async def test_analyze_calls_llm(analyzer, sample_news):
    mock_response = '{"trend_summary": "Today saw major releases in LLM space.", "categorized_news": [{"title": "GPT-5 Released", "summary": "OpenAI released GPT-5", "category": "大模型", "source": "hackernews", "url": "https://example.com/gpt5"}, {"title": "New open source LLM", "summary": "Community releases new model", "category": "开源", "source": "reddit", "url": "https://example.com/llm"}]}'
    with patch("app.analyzer.llm_analyzer.acompletion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value.choices = [
            type("Choice", (), {"message": type("Msg", (), {"content": mock_response})()})()
        ]
        result = await analyzer.analyze(sample_news)
        assert result is not None
        assert result.trend_summary == "Today saw major releases in LLM space."
        assert len(result.categorized_news) == 2
        assert mock_llm.called


@pytest.mark.asyncio
async def test_analyze_empty_list(analyzer):
    result = await analyzer.analyze([])
    assert result.trend_summary == ""
    assert result.categorized_news == []
