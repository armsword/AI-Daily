import pytest
from pathlib import Path
from PIL import Image
from app.renderer.pillow_renderer import PillowInfographicRenderer
from app.analyzer.llm_analyzer import AnalysisResult


@pytest.fixture
def renderer():
    return PillowInfographicRenderer()


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        trend_summary="AI领域今日有重大突破，多家公司发布新模型",
        categorized_news=[
            {"title": "GPT-5 Released", "summary": "OpenAI发布GPT-5大模型", "category": "大模型", "source": "hackernews", "url": "https://example.com/1"},
            {"title": "开源新模型发布", "summary": "社区发布新开源模型", "category": "开源", "source": "reddit", "url": "https://example.com/2"},
            {"title": "AI医疗应用突破", "summary": "AI辅助诊断准确率提升", "category": "应用", "source": "hackernews", "url": "https://example.com/3"},
        ],
    )


def test_render_creates_png(renderer, sample_analysis, tmp_path):
    result = renderer.render(
        date="2026-05-07",
        analysis=sample_analysis,
        output_dir=str(tmp_path),
    )
    assert result.endswith(".png")
    assert Path(result).exists()
    img = Image.open(result)
    assert img.width > 0
    assert img.height > 0


def test_render_image_dimensions(renderer, sample_analysis, tmp_path):
    result = renderer.render(
        date="2026-05-07",
        analysis=sample_analysis,
        output_dir=str(tmp_path),
    )
    img = Image.open(result)
    # 竖版长图，宽度应在 800 左右
    assert 700 <= img.width <= 900
    # 高度应大于宽度（竖版）
    assert img.height > img.width


def test_render_output_filename(renderer, sample_analysis, tmp_path):
    result = renderer.render(
        date="2026-05-07",
        analysis=sample_analysis,
        output_dir=str(tmp_path),
    )
    assert result == str(tmp_path / "2026-05-07.png")


def test_render_creates_output_dir(renderer, sample_analysis, tmp_path):
    nested = str(tmp_path / "sub" / "dir")
    result = renderer.render(
        date="2026-05-07",
        analysis=sample_analysis,
        output_dir=nested,
    )
    assert Path(result).exists()


def test_render_with_many_news(renderer, tmp_path):
    news = [
        {"title": f"News {i}", "summary": f"新闻摘要{i}", "category": "大模型", "source": "hackernews", "url": f"https://example.com/{i}"}
        for i in range(8)
    ]
    analysis = AnalysisResult(trend_summary="今日趋势总结", categorized_news=news)
    result = renderer.render(
        date="2026-05-07",
        analysis=analysis,
        output_dir=str(tmp_path),
    )
    assert Path(result).exists()
