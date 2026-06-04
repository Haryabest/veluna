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


class CivitaiProvider(ImageGenerationProvider):
    BASE_URL = "https://orchestration.civitai.com/api/v1"

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.civitai_api_key

    @property
    def provider_name(self) -> str:
        return "civitai"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        async with httpx.AsyncClient() as client:
            create_resp = await client.post(
                f"{self.BASE_URL}/image/create",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": request.prompt,
                    "negativePrompt": request.negative_prompt or "",
                    "model": request.model or "urn:air:sd1:checkpoint:civitai:101055@762648",
                    "width": request.width,
                    "height": request.height,
                    "steps": request.num_inference_steps,
                    "quantity": 1,
                },
                timeout=30.0,
            )
            create_resp.raise_for_status()
            job = create_resp.json()
            job_id = job.get("jobId") or job.get("id")
            if not job_id:
                raise RuntimeError(f"CivitAI did not return a job ID: {job}")

            import asyncio
            for _ in range(60):
                await asyncio.sleep(2)
                status_resp = await client.get(
                    f"{self.BASE_URL}/image/status/{job_id}",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=30.0,
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()
                state = status_data.get("status") or status_data.get("state", "")
                if state in ("succeeded", "completed", "done"):
                    images = status_data.get("images") or status_data.get("results") or []
                    image_url = images[0].get("url") if images else ""
                    if not image_url and isinstance(images, list) and images:
                        image_url = images[0] if isinstance(images[0], str) else ""
                    return ImageGenerationResponse(
                        image_url=image_url,
                        provider=self.provider_name,
                        metadata={"job_id": job_id},
                    )
                if state in ("failed", "error", "cancelled"):
                    raise RuntimeError(f"CivitAI job {job_id} {state}: {status_data}")

            raise TimeoutError(f"CivitAI job {job_id} timed out after 120s")

    async def health_check(self) -> bool:
        return bool(self._api_key)
