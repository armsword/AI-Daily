import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from PIL import Image
import io
from app.renderer.image_generator import NanoBananaImageGenerator
from app.analyzer.llm_analyzer import AnalysisResult


@pytest.fixture
def generator():
    return NanoBananaImageGenerator(api_key="test-key")


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        trend_summary="AI领域今日有重大突破",
        categorized_news=[
            {"title": "GPT-5 Released", "summary": "OpenAI发布GPT-5", "category": "大模型", "source": "hackernews", "url": "https://example.com/1"},
            {"title": "开源新模型", "summary": "社区发布新模型", "category": "开源", "source": "reddit", "url": "https://example.com/2"},
        ],
    )


def _make_fake_image_bytes() -> bytes:
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_build_prompt_contains_news(generator, sample_analysis):
    prompt = generator._build_prompt("2026-05-08", sample_analysis)
    assert "GPT-5" in prompt
    assert "大模型" in prompt
    assert "2026-05-08" in prompt
    assert "AI日报" in prompt


def test_build_prompt_contains_summary(generator, sample_analysis):
    prompt = generator._build_prompt("2026-05-08", sample_analysis)
    assert "AI领域今日有重大突破" in prompt


@pytest.mark.asyncio
async def test_generate_saves_image(generator, sample_analysis, tmp_path):
    fake_bytes = _make_fake_image_bytes()

    mock_part = MagicMock()
    mock_part.text = None
    mock_part.inline_data = MagicMock()
    mock_part.inline_data.data = fake_bytes

    mock_response = MagicMock()
    mock_response.parts = [mock_part]

    with patch("app.renderer.image_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )

        assert result.endswith("2026-05-08.png")
        assert Path(result).exists()
        mock_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_generate_returns_empty_on_failure(generator, sample_analysis, tmp_path):
    with patch("app.renderer.image_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")
        mock_genai.Client.return_value = mock_client

        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )
        assert result == ""


@pytest.mark.asyncio
async def test_generate_no_image_in_response(generator, sample_analysis, tmp_path):
    mock_part = MagicMock()
    mock_part.text = "Here is a description"
    mock_part.inline_data = None

    mock_response = MagicMock()
    mock_response.parts = [mock_part]

    with patch("app.renderer.image_generator.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )
        assert result == ""
