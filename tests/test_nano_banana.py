import pytest
import httpx
import respx
from pathlib import Path
from app.renderer.image_generator import NanoBananaImageGenerator
from app.analyzer.llm_analyzer import AnalysisResult


@pytest.fixture
def generator():
    return NanoBananaImageGenerator(
        api_key="test-key",
        api_base="https://visionary.beer",
    )


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        trend_summary="AI领域今日有重大突破",
        categorized_news=[
            {"title": "GPT-5 Released", "summary": "OpenAI发布GPT-5", "category": "大模型", "source": "hackernews", "url": "https://example.com/1"},
            {"title": "开源新模型", "summary": "社区发布新模型", "category": "开源", "source": "reddit", "url": "https://example.com/2"},
        ],
    )


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
    fake_image_url = "https://visionary.beer/openapi-assets/test.png"
    fake_image_bytes = b"\x89PNG\r\n\x1a\nfake-image-data"

    with respx.mock:
        respx.post("https://visionary.beer/openapi/v1/images/generations").mock(
            return_value=httpx.Response(200, json={
                "id": "test-id",
                "results": [{"url": fake_image_url, "content": ""}],
                "status": "succeeded",
                "progress": 100,
            })
        )
        respx.get(fake_image_url).mock(
            return_value=httpx.Response(200, content=fake_image_bytes)
        )

        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )

        assert result.endswith("2026-05-08.png")
        assert Path(result).exists()
        assert Path(result).read_bytes() == fake_image_bytes


@pytest.mark.asyncio
async def test_generate_returns_empty_on_api_error(generator, sample_analysis, tmp_path):
    with respx.mock:
        respx.post("https://visionary.beer/openapi/v1/images/generations").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )

        result = await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )
        assert result == ""


@pytest.mark.asyncio
async def test_generate_sends_correct_payload(generator, sample_analysis, tmp_path):
    fake_image_url = "https://visionary.beer/openapi-assets/test.png"

    with respx.mock:
        route = respx.post("https://visionary.beer/openapi/v1/images/generations").mock(
            return_value=httpx.Response(200, json={
                "id": "test-id",
                "results": [{"url": fake_image_url, "content": ""}],
                "status": "succeeded",
                "progress": 100,
            })
        )
        respx.get(fake_image_url).mock(
            return_value=httpx.Response(200, content=b"img")
        )

        await generator.generate_daily_image(
            date="2026-05-08",
            analysis=sample_analysis,
            output_dir=str(tmp_path),
        )

        import json
        body = json.loads(route.calls[0].request.content)
        assert body["model"] == "Nano_Banana_Pro"
        assert body["ratio"] == "9:16"
        assert "GPT-5" in body["prompt"]

        auth = route.calls[0].request.headers["authorization"]
        assert auth == "Bearer test-key"
