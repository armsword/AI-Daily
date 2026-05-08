import pytest
import httpx
import respx
import base64
from pathlib import Path
from app.renderer.image_generator import MiniMaxImageGenerator


@pytest.fixture
def generator():
    return MiniMaxImageGenerator(
        api_key="test-key",
        api_base="https://api.minimaxi.com",
    )


@pytest.mark.asyncio
async def test_generate_cover_success(generator, tmp_path):
    fake_image = base64.b64encode(b"fake-png-data").decode()
    with respx.mock:
        respx.post("https://api.minimaxi.com/v1/image_generation").mock(
            return_value=httpx.Response(200, json={
                "data": {"image_base64": [fake_image]}
            })
        )
        result = await generator.generate_cover(
            summary="AI领域今日重大突破",
            date="2026-05-08",
            output_dir=str(tmp_path),
        )
        assert result != ""
        assert Path(result).exists()
        assert result.endswith("-cover.png")


@pytest.mark.asyncio
async def test_generate_cover_api_failure(generator, tmp_path):
    with respx.mock:
        respx.post("https://api.minimaxi.com/v1/image_generation").mock(
            return_value=httpx.Response(500, json={"error": "server error"})
        )
        result = await generator.generate_cover(
            summary="test",
            date="2026-05-08",
            output_dir=str(tmp_path),
        )
        assert result == ""


@pytest.mark.asyncio
async def test_generate_cover_builds_prompt(generator, tmp_path):
    fake_image = base64.b64encode(b"fake-png-data").decode()
    with respx.mock:
        route = respx.post("https://api.minimaxi.com/v1/image_generation").mock(
            return_value=httpx.Response(200, json={
                "data": {"image_base64": [fake_image]}
            })
        )
        await generator.generate_cover(
            summary="大模型训练加速，开源社区活跃",
            date="2026-05-08",
            output_dir=str(tmp_path),
        )
        request_body = route.calls[0].request
        import json
        body = json.loads(request_body.content)
        assert body["model"] == "image-01"
        assert "16:9" in body["aspect_ratio"]
        assert len(body["prompt"]) > 0
