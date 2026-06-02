from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 768
    num_inference_steps: int = 28
    seed: int | None = None
    model: str | None = None


@dataclass
class ImageGenerationResponse:
    image_url: str
    provider: str
    metadata: dict = field(default_factory=dict)


class ImageGenerationProvider(ABC):
    @abstractmethod
    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
