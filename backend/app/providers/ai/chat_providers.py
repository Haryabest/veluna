import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.providers.ai.base import (
    AIChatProvider,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)


class OpenAIProvider(AIChatProvider):
    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_model

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend({"role": m.role, "content": m.content} for m in request.messages)

        response = await self._client.chat.completions.create(
            model=request.model or self._model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        choice = response.choices[0]
        return ChatCompletionResponse(
            content=choice.message.content or "",
            tokens_used=response.usage.total_tokens if response.usage else 0,
            model=response.model,
            finish_reason=choice.finish_reason or "stop",
        )

    async def health_check(self) -> bool:
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False


class OpenRouterProvider(AIChatProvider):
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend({"role": m.role, "content": m.content} for m in request.messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": request.model or self._model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        return ChatCompletionResponse(
            content=choice["message"]["content"],
            tokens_used=usage.get("total_tokens", 0),
            model=data.get("model", self._model),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def health_check(self) -> bool:
        return bool(self._api_key)


class GroqProvider(AIChatProvider):
    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._model = settings.groq_model

    @property
    def provider_name(self) -> str:
        return "groq"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.extend({"role": m.role, "content": m.content} for m in request.messages)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": request.model or self._model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        return ChatCompletionResponse(
            content=choice["message"]["content"],
            tokens_used=usage.get("total_tokens", 0),
            model=data.get("model", self._model),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def health_check(self) -> bool:
        return bool(self._api_key)
