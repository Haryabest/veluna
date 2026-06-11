"""Z-Image image generation via gen-api.ru.

Docs: https://gen-api.ru/model/z-image/api
Long-polling: GET https://api.gen-api.ru/api/v1/request/get/{request_id}

    POST https://api.gen-api.ru/api/v1/networks/z-image
    {"prompt": "<prompt>"}
    -> {"request_id": ..., "status": "processing"}
    -> poll until status == "success", image in result[]
The bearer token is the same GEN_API_KEY we use for chat completions.
"""

import asyncio
import base64
import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.ai._response_helpers import extract_image_url
from app.providers.ai.image_base import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResponse,
)

logger = logging.getLogger(__name__)

# gen-api returns an inline b64 string when b64_json is requested. We don't
# request that, but if some other code path does, expose it as a data: URL so
# the existing download/upload pipeline in generation_tasks.py keeps working.
_GENAPI_POLL_BASE = "https://api.gen-api.ru/api/v1/request/get"
_POLL_INTERVAL_SECONDS = 2.0
_DATA_URL_PREFIX = "data:image/"


class ZImageProvider(ImageGenerationProvider):
    DEFAULT_MODEL_NAME = "Z-Image"

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.gen_api_key.strip()
        self._base_url = settings.zimage_base_url.rstrip("/")
        self._timeout = settings.zimage_timeout_seconds

    @property
    def provider_name(self) -> str:
        return "zimage"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        if not self._api_key:
            raise ValueError("GEN_API_KEY is empty — cannot call Z-Image")

        body: dict[str, Any] = {
            "prompt": request.prompt,
        }
        if request.width:
            body["width"] = request.width
        if request.height:
            body["height"] = request.height
        if request.seed is not None:
            body["seed"] = request.seed

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._base_url,
                headers=headers,
                json=body,
                timeout=self._timeout,
            )
            if response.status_code >= 400:
                raise ValueError(self._format_error(response))
            data = response.json()

            if data.get("status") == "processing" or not self._extract_image(data):
                request_id = data.get("request_id")
                if not request_id:
                    raise ValueError("Z-Image response did not contain request_id")
                data = await self._poll_until_ready(client, request_id, headers)

        image_url = self._extract_image(data)
        if not image_url:
            logger.warning("Z-Image response had no recognisable image URL: %s", data)
            raise ValueError("Z-Image response did not contain an image URL")

        return ImageGenerationResponse(
            image_url=image_url,
            provider=self.provider_name,
            metadata={
                "model_name": self.DEFAULT_MODEL_NAME,
                "requested_model": request.model,
                "request_id": data.get("request_id") or data.get("id"),
            },
        )

    def _extract_image(self, data: Any) -> str | None:
        url = extract_image_url(data)
        if url:
            return url
        b64 = self._extract_b64(data)
        if b64:
            return f"{_DATA_URL_PREFIX}png;base64,{b64}"
        return None

    async def _poll_until_ready(
        self,
        client: httpx.AsyncClient,
        request_id: int | str,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        deadline = time.monotonic() + self._timeout
        poll_url = f"{_GENAPI_POLL_BASE}/{request_id}"

        while time.monotonic() < deadline:
            response = await client.get(poll_url, headers=headers, timeout=60.0)
            if response.status_code >= 400:
                raise ValueError(self._format_error(response))
            data = response.json()
            status = data.get("status")

            if status == "success":
                return data
            if status in ("failed", "error"):
                message = data.get("message") or data.get("error") or data
                raise ValueError(f"Z-Image generation failed: {message}")

            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

        raise ValueError(
            f"Z-Image generation timed out after {int(self._timeout)}s (request_id={request_id})"
        )

    @staticmethod
    def _extract_b64(data: Any) -> str | None:
        """Find a base64 image payload in the response, if present."""

        def _walk(node: Any) -> str | None:
            if isinstance(node, str):
                # Heuristic: very long strings that decode as base64 and
                # start with a PNG/JPEG/WebP signature.
                if len(node) > 1024:
                    try:
                        raw = base64.b64decode(node, validate=False)
                    except Exception:
                        return None
                    if raw.startswith(b"\x89PNG\r\n\xa1\n") or raw.startswith(b"\xff\xd8\xff") or raw.startswith(b"RIFF"):
                        return node
                return None
            if isinstance(node, dict):
                for key in ("b64_json", "image", "image_b64", "image_base64"):
                    value = node.get(key)
                    found = _walk(value)
                    if found:
                        return found
                for value in node.values():
                    found = _walk(value)
                    if found:
                        return found
            if isinstance(node, list):
                for item in node:
                    found = _walk(item)
                    if found:
                        return found
            return None

        return _walk(data)

    @staticmethod
    def _format_error(response: httpx.Response) -> str:
        text = response.text[:1000]
        logger.warning("Z-Image error response: status=%s body=%s", response.status_code, text)
        try:
            data = response.json()
            if isinstance(data, dict):
                errors = data.get("errors_validation")
                if isinstance(errors, dict) and errors:
                    return f"Z-Image API error {response.status_code}: {errors}"
                for key in ("error", "message", "detail", "title"):
                    value = data.get(key)
                    if isinstance(value, str) and value:
                        return f"Z-Image API error {response.status_code}: {value}"
                if data.get("error") is True:
                    return f"Z-Image API error {response.status_code}: {data}"
        except ValueError:
            pass
        return f"Z-Image API error {response.status_code}: {text}"

    async def health_check(self) -> bool:
        return bool(self._api_key)
