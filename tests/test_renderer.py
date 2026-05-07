import pytest
from pathlib import Path
from app.renderer.card_renderer import CardRenderer
from app.analyzer.llm_analyzer import AnalysisResult


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        trend_summary="今天AI领域有重大突破，多个开源模型发布。",
        categorized_news=[
            {"title": "GPT-5 Released", "summary": "OpenAI发布了GPT-5", "category": "大模型", "source": "hackernews", "url": "https://example.com/1"},
            {"title": "New OS Model", "summary": "社区发布新开源模型", "category": "开源", "source": "reddit", "url": "https://example.com/2"},
        ],
    )


@pytest.fixture
def renderer(tmp_path):
    return CardRenderer(output_dir=str(tmp_path), card_width=800)


def test_render_html(renderer, sample_analysis):
    html = renderer.render_html("2026-05-07", sample_analysis)
    assert "2026-05-07" in html
    assert "GPT-5 Released" in html
    assert "今天AI领域" in html


def test_render_card_creates_file(renderer, sample_analysis):
    output_path = renderer.render_card("2026-05-07", sample_analysis)
    assert Path(output_path).exists()
    assert output_path.endswith(".png")
