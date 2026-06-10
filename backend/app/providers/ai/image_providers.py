import asyncio
import logging
from typing import Any
import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
from app.utils.civitai_air import (
    ecosystem_from_air,
    resolve_civitai_model_air,
    resolve_civitai_model_label,
    resource_type_from_air,
)
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
    def __init__(self):
        settings = get_settings()
        self._api_key = settings.civitai_api_key
        self._proxy = (settings.civitai_http_proxy or "").strip() or None

    def _client(self) -> httpx.AsyncClient:
        """Build an AsyncClient, routing through the configured proxy if any."""
        return httpx.AsyncClient(proxy=self._proxy) if self._proxy else httpx.AsyncClient()

    @property
    def provider_name(self) -> str:
        return "civitai"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        model_urn = await resolve_civitai_model_air(request.model, proxy=self._proxy)
        model_label = await resolve_civitai_model_label(request.model)
        resource_type = resource_type_from_air(model_urn)
        if resource_type and resource_type != "checkpoint":
            raise ValueError(
                f"«{model_label}» — это {resource_type}, а не checkpoint. "
                "Для генерации нужна полноценная модель (Checkpoint), не LoRA/Embedding."
            )
        ecosystem = ecosystem_from_air(model_urn)
        if not model_urn:
            raise ValueError("Civitai model is required")

        return await self._generate_v2_workflow(
            request,
            model_urn=model_urn,
            model_label=model_label,
            ecosystem=ecosystem,
        )

    async def _generate_v2_workflow(
        self,
        request: ImageGenerationRequest,
        *,
        model_urn: str,
        model_label: str,
        ecosystem: str,
    ) -> ImageGenerationResponse:
        # SFW only; Buzz: blue → green → yellow (Civitai default, no currencies filter).
        #
        # Engines (per Civitai Orchestration v2 docs, https://developer.civitai.com/orchestration/):
        #   - comfy   → works on blue/green/yellow. Default choice for most ecosystems.
        #   - sdcpp   → only on yellow tier. Returns misleading "insufficientBuzz" on green.
        #   - flux1-kontext → for the flux1 ecosystem with model = dev/pro/max tier string.
        #
        # Default = "comfy" so green tier tokens (the common case) actually work.
        engine = self._pick_engine(request, ecosystem)
        body: dict[str, Any] = {
            "allowMatureContent": False,
            "steps": [{
                "$type": "imageGen",
                "input": {
                    "engine": engine,
                    "ecosystem": ecosystem,
                    "operation": "createImage",
                    "model": model_urn,
                    "prompt": request.prompt,
                    "negativePrompt": request.negative_prompt or "",
                    "width": request.width or 1024,
                    "height": request.height or 1024,
                    "cfgScale": 4 if ecosystem == "anima" else 7,
                    "steps": request.num_inference_steps or (30 if ecosystem == "anima" else 28),
                    "quantity": 1,
                },
            }],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with self._client() as client:
            submit_resp = await client.post(
                "https://orchestration.civitai.com/v2/consumer/workflows?wait=90&hideMatureContent=true",
                headers=headers,
                json=body,
                timeout=120.0,
            )
            if submit_resp.status_code >= 400:
                raise ValueError(
                    self._format_v2_error(submit_resp, engine=engine, ecosystem=ecosystem)
                )

            workflow = submit_resp.json()
            workflow_id = workflow.get("id", "")
            image_url = self._extract_workflow_image_url(workflow)
            if image_url:
                return self._image_response(image_url, model_label, model_urn, request.model, workflow_id)

            for _ in range(45):
                await asyncio.sleep(2)
                poll_resp = await client.get(
                    f"https://orchestration.civitai.com/v2/consumer/workflows/{workflow_id}",
                    headers=headers,
                    timeout=30.0,
                )
                poll_resp.raise_for_status()
                workflow = poll_resp.json()
                image_url = self._extract_workflow_image_url(workflow)
                if image_url:
                    return self._image_response(image_url, model_label, model_urn, request.model, workflow_id)
                if workflow.get("status") in {"failed", "canceled"}:
                    raise RuntimeError(f"Civitai workflow {workflow_id} {workflow.get('status')}: {workflow}")

        raise TimeoutError(f"Civitai workflow {workflow_id} timed out")

    def _image_response(
        self,
        image_url: str,
        model_label: str,
        model_urn: str,
        requested_model: str | None,
        workflow_id: str | None = None,
    ) -> ImageGenerationResponse:
        metadata: dict[str, Any] = {
            "model_name": model_label,
            "model_air": model_urn,
            "requested_model": requested_model,
        }
        if workflow_id:
            metadata["workflow_id"] = workflow_id
        return ImageGenerationResponse(
            image_url=image_url,
            provider=self.provider_name,
            metadata=metadata,
        )

    def _extract_workflow_image_url(self, workflow: dict[str, Any]) -> str | None:
        for step in workflow.get("steps", []):
            output = step.get("output") if isinstance(step, dict) else None
            if not isinstance(output, dict):
                continue
            for collection_key in ("images", "blobs"):
                collection = output.get(collection_key)
                if isinstance(collection, list):
                    for item in collection:
                        found = self._extract_sdk_image_url(item)
                        if found:
                            return found
        return None

    def _extract_sdk_image_url(self, response: Any) -> str | None:
        if isinstance(response, str):
            return response if response.startswith(("http://", "https://")) else None

        if isinstance(response, dict):
            for key in ("url", "imageUrl", "blobUrl", "previewUrl", "downloadUrl"):
                value = response.get(key)
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    return value

            result = response.get("result")
            if result:
                found = self._extract_sdk_image_url(result)
                if found:
                    return found

            for collection_key in ("jobs", "images", "blobs", "outputs"):
                collection = response.get(collection_key)
                if isinstance(collection, list):
                    for item in collection:
                        found = self._extract_sdk_image_url(item)
                        if found:
                            return found

            for value in response.values():
                if isinstance(value, (dict, list)):
                    found = self._extract_sdk_image_url(value)
                    if found:
                        return found

        if isinstance(response, list):
            for item in response:
                found = self._extract_sdk_image_url(item)
                if found:
                    return found

        if hasattr(response, "model_dump"):
            return self._extract_sdk_image_url(response.model_dump())

        for key in ("url", "imageUrl", "blobUrl", "previewUrl", "downloadUrl", "result"):
            if hasattr(response, key):
                found = self._extract_sdk_image_url(getattr(response, key))
                if found:
                    return found

        return None

    def _pick_engine(self, request: ImageGenerationRequest, ecosystem: str) -> str:
        """Pick a Civitai Orchestration engine.

        "engine" is a discriminator in the Orchestration v2 schema; values
        not listed in the docs trigger "No derived type found" errors.
        See https://developer.civitai.com/orchestration/ for the full list.
        comfy is the only engine that works across blue/green/yellow tiers.
        """
        if request.engine:
            return request.engine

        settings = get_settings()
        return getattr(settings, "civitai_default_engine", "comfy") or "comfy"

    def _format_v2_error(
        self,
        response: httpx.Response,
        *,
        engine: str | None = None,
        ecosystem: str | None = None,
    ) -> str:
        # Always log the full body for diagnostics — Civitai returns multiple shapes
        # (sometimes `insufficientBuzz: true`, sometimes `{transactions: {…}}`,
        # sometimes a list of strings, sometimes a bare `error` string).
        raw_text = response.text[:1000]
        logger.warning(
            "Civitai v2 error response: status=%s engine=%s ecosystem=%s body=%s",
            response.status_code,
            engine,
            ecosystem,
            raw_text,
        )

        def _insufficient_buzz_hint() -> str:
            base = (
                "На Civitai API токене недостаточно Buzz для генерации. "
                "Проверьте баланс (blue/green/yellow) аккаунта Civitai для этого API токена."
            )
            # sdcpp is yellow-only — on green it returns this misleading error.
            if engine == "sdcpp":
                base += (
                    "\nДвижок «sdcpp» входит только в yellow-тариф Civitai. "
                    "Для green-tier установите CIVITAI_DEFAULT_ENGINE=comfy в .env."
                )
            elif engine and engine not in {"comfy"}:
                base += (
                    f"\nДвижок «{engine}» может не поддерживаться на текущем тарифе. "
                    "Попробуйте CIVITAI_DEFAULT_ENGINE=comfy в .env."
                )
            return base

        try:
            data = response.json()
        except ValueError:
            return f"Civitai API error {response.status_code}: {raw_text}"

        # Case 1: response is not a dict (e.g. bare string, list).
        if not isinstance(data, dict):
            text = str(data)
            if "insufficient" in text.lower() and "buzz" in text.lower():
                return _insufficient_buzz_hint()
            return f"Civitai API error {response.status_code}: {text[:500]}"

        # Case 2: explicit insufficientBuzz flag (top-level or nested in transactions).
        transactions = data.get("transactions") if isinstance(data.get("transactions"), dict) else {}
        if transactions.get("insufficientBuzz") or data.get("insufficientBuzz"):
            return _insufficient_buzz_hint()

        # Case 3: errors array (Civitai's standard validation-error shape).
        errors = data.get("errors")
        if errors:
            return f"Civitai отклонил запрос генерации: {errors}"

        # Case 4: bare "error"/"message" string sometimes used by the API.
        bare = data.get("error") or data.get("message")
        if isinstance(bare, str) and bare:
            if "insufficient" in bare.lower() and "buzz" in bare.lower():
                return _insufficient_buzz_hint()
            return f"Civitai API error {response.status_code}: {bare}"

        title = data.get("title") or data.get("detail")
        if title:
            return f"Civitai API error {response.status_code}: {title}"

        return f"Civitai API error {response.status_code}: {str(data)[:500]}"

    async def health_check(self) -> bool:
        return bool(self._api_key)
