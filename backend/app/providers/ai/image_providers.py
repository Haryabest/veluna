import httpx

from app.core.config import get_settings
from app.utils.civitai_air import ecosystem_from_air, resolve_civitai_model_air
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
    BASE_URL = "https://orchestration.civitai.com/v2"

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.civitai_api_key

    @property
    def provider_name(self) -> str:
        return "civitai"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        import asyncio

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        model_urn = await resolve_civitai_model_air(request.model)
        ecosystem = ecosystem_from_air(model_urn)
        body: dict = {
            "steps": [{
                "$type": "imageGen",
                "input": {
                    "engine": "sdcpp",
                    "ecosystem": ecosystem,
                    "operation": "createImage",
                    "prompt": request.prompt,
                    "negativePrompt": request.negative_prompt or "",
                    "width": request.width or 1024,
                    "height": request.height or 1024,
                    "cfgScale": 7,
                    "steps": request.num_inference_steps or 25,
                    "quantity": 1,
                },
            }],
        }

        if model_urn:
            body["steps"][0]["input"]["model"] = model_urn

        async with httpx.AsyncClient() as client:
            submit_resp = await client.post(
                f"{self.BASE_URL}/consumer/workflows?wait=90",
                headers=headers,
                json=body,
                timeout=120.0,
            )
            submit_resp.raise_for_status()
            wf = submit_resp.json()

            wf_id = wf.get("id", "")
            status = wf.get("status", "")

            if status == "succeeded":
                return self._extract_image(wf, wf_id)

            for _ in range(45):
                await asyncio.sleep(2)
                poll_resp = await client.get(
                    f"{self.BASE_URL}/consumer/workflows/{wf_id}",
                    headers=headers,
                    timeout=30.0,
                )
                poll_resp.raise_for_status()
                wf = poll_resp.json()
                status = wf.get("status", "")
                if status == "succeeded":
                    return self._extract_image(wf, wf_id)
                if status in ("failed", "canceled"):
                    err = wf.get("error", str(wf))
                    raise RuntimeError(f"CivitAI workflow {wf_id} {status}: {err}")

            raise TimeoutError(f"CivitAI workflow {wf_id} timed out")

    def _extract_image(self, wf: dict, wf_id: str) -> ImageGenerationResponse:
        steps = wf.get("steps", [])
        for step in steps:
            output = step.get("output", {})
            blobs = output.get("blobs", [])
            for blob in blobs:
                url = blob.get("url", "")
                if url:
                    return ImageGenerationResponse(
                        image_url=url,
                        provider=self.provider_name,
                        metadata={"workflow_id": wf_id},
                    )
        raise RuntimeError(f"CivitAI workflow {wf_id} succeeded but no image URL found")

    async def health_check(self) -> bool:
        return bool(self._api_key)
