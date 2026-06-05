from openai import AsyncOpenAI

from app.core.config import get_settings
from app.providers.ai.base import (
    AIChatProvider,
    ChatCompletionRequest,
    ChatCompletionResponse,
)


class GenApiProvider(AIChatProvider):
    """GenAPI GPT-4o mini via OpenAI-compatible proxy (https://gen-api.ru/docs)."""

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.gen_api_key,
            base_url=settings.gen_api_base_url.rstrip("/"),
        )
        self._model = settings.gen_api_model

    @property
    def provider_name(self) -> str:
        return "genapi"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        messages: list[dict[str, str]] = []
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
        settings = get_settings()
        return bool(settings.gen_api_key.strip())
