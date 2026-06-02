from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatCompletionRequest:
    messages: list[ChatMessage]
    system_prompt: str = ""
    max_tokens: int = 1024
    temperature: float = 0.8
    model: str | None = None


@dataclass
class ChatCompletionResponse:
    content: str
    tokens_used: int
    model: str
    finish_reason: str = "stop"
    metadata: dict = field(default_factory=dict)


class AIChatProvider(ABC):
    @abstractmethod
    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
