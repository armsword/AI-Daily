import base64
import logging
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

COVER_PROMPT_TEMPLATE = (
    "A futuristic digital art illustration representing today's AI news: {summary}. "
    "Style: clean, modern, tech-themed, dark background with glowing cyan and purple accents, "
    "abstract neural network patterns, minimalist composition. No text or letters in the image."
)


class MiniMaxImageGenerator:
    def __init__(self, api_key: str, api_base: str = "https://api.minimaxi.com"):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")

    async def generate_cover(self, summary: str, date: str, output_dir: str) -> str:
        prompt = COVER_PROMPT_TEMPLATE.format(summary=summary[:200])
        url = f"{self.api_base}/v1/image_generation"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "image-01",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "response_format": "base64",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            image_b64 = data["data"]["image_base64"][0]
            image_bytes = base64.b64decode(image_b64)

            Path(output_dir).mkdir(parents=True, exist_ok=True)
            filename = f"{date}-cover.png"
            output_path = str(Path(output_dir) / filename)
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Cover image generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"MiniMax image generation failed: {e}")
            return ""
