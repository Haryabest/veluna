from app.providers.ai.base import (
    AIChatProvider,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)


class StubChatProvider(AIChatProvider):
    """Fallback when no external AI API key is configured (local dev)."""

    @property
    def provider_name(self) -> str:
        return "stub"

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        last_user: ChatMessage | None = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_user = msg
                break
        if last_user:
            snippet = last_user.content.strip()
            if len(snippet) > 160:
                snippet = snippet[:157] + "…"
            reply = f"Я услышала тебя: «{snippet}». (Ответы AI пока не подключены — добавьте ключ в .env.)"
        else:
            reply = "Привет! Я на связи. (Режим без внешнего AI.)"
        return ChatCompletionResponse(content=reply, tokens_used=0, model="stub")

    async def health_check(self) -> bool:
        return True
