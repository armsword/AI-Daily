import pytest
import httpx
import respx
import base64
import json
from pathlib import Path
from app.renderer.image_generator import MiniMaxImageGenerator
from app.analyzer.llm_analyzer import AnalysisResult


@pytest.fixture
def generator():
    return MiniMaxImageGenerator(
        api_key="test-key",
        api_base="https://api.minimaxi.com",
    )


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        trend_summary="AI领域今日有重大突破",
        categorized_news=[
            {"title": "GPT-5 Released", "summary": "OpenAI发布GPT-5", "category": "大模型", "source": "hackernews", "url": "https://example.com/1"},
            {"title": "New OS Model", "summary": "社区发布新模型", "category": "开源", "source": "reddit", "url": "https://example.com/2"},
        ],
    )


@pytest.mark.asyncio
async def test_generate_daily_image_success(generator, sample_analysis, tmp_path):
    fake_image = base64.b64encode(b"fake-png-data").decode()
    with respx.mock:
        respx.post("https://api.minimaxi.com/v1/image_generation").mock(
            return_value=httpx.Response(200, json={
                "data": {"image_base64": [fake_image]},
                "base_resp": {"status_code": 0, "status_msg": "success"},
            })
        )
        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )
        assert result != ""
        assert Path(result).exists()
        assert result.endswith("2026-05-08.png")


@pytest.mark.asyncio
async def test_generate_daily_image_api_failure(generator, sample_analysis, tmp_path):
    with respx.mock:
        respx.post("https://api.minimaxi.com/v1/image_generation").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )
        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )
        assert result == ""


@pytest.mark.asyncio
async def test_prompt_contains_news_content(generator, sample_analysis, tmp_path):
    fake_image = base64.b64encode(b"fake-png-data").decode()
    with respx.mock:
        route = respx.post("https://api.minimaxi.com/v1/image_generation").mock(
            return_value=httpx.Response(200, json={
                "data": {"image_base64": [fake_image]},
                "base_resp": {"status_code": 0, "status_msg": "success"},
            })
        )
        await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )
        body = json.loads(route.calls[0].request.content)
        assert body["model"] == "image-01"
        assert body["aspect_ratio"] == "9:16"
        assert "GPT-5" in body["prompt"]
        assert "大模型" in body["prompt"]
