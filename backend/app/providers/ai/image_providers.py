import httpx

from app.core.config import get_settings
from app.providers.ai.image_base import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResponse,
)


class FalProvider(ImageGenerationProvider):
    BASE_URL = "https://fal.run"

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.fal_api_key
        self._model = "fal-ai/flux/dev"

    @property
    def provider_name(self) -> str:
        return "fal"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{request.model or self._model}",
                headers={"Authorization": f"Key {self._api_key}"},
                json={
                    "prompt": request.prompt,
                    "negative_prompt": request.negative_prompt,
                    "image_size": {"width": request.width, "height": request.height},
                    "num_inference_steps": request.num_inference_steps,
                    "seed": request.seed,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

        images = data.get("images", [])
        image_url = images[0]["url"] if images else ""
        return ImageGenerationResponse(
            image_url=image_url,
            provider=self.provider_name,
            metadata={"request_id": data.get("request_id")},
        )

    async def health_check(self) -> bool:
        return bool(self._api_key)


class ReplicateProvider(ImageGenerationProvider):
    BASE_URL = "https://api.replicate.com/v1"

    def __init__(self):
        settings = get_settings()
        self._api_token = settings.replicate_api_token
        self._model = "black-forest-labs/flux-dev"

    @property
    def provider_name(self) -> str:
        return "replicate"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/predictions",
                headers={"Authorization": f"Token {self._api_token}"},
                json={
                    "version": request.model or self._model,
                    "input": {
                        "prompt": request.prompt,
                        "negative_prompt": request.negative_prompt,
                        "width": request.width,
                        "height": request.height,
                        "num_inference_steps": request.num_inference_steps,
                    },
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

        output = data.get("output", [])
        image_url = output[0] if isinstance(output, list) and output else str(output)
        return ImageGenerationResponse(
            image_url=image_url,
            provider=self.provider_name,
            metadata={"prediction_id": data.get("id")},
        )

    async def health_check(self) -> bool:
        return bool(self._api_token)
