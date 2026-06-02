from functools import lru_cache

from app.core.config import get_settings
from app.providers.ai.base import AIChatProvider
from app.providers.ai.chat_providers import GroqProvider, OpenAIProvider, OpenRouterProvider
from app.providers.ai.image_base import ImageGenerationProvider
from app.providers.ai.image_providers import FalProvider, ReplicateProvider
from app.providers.storage.base import StorageProvider
from app.providers.storage.providers import MinioStorageProvider, S3StorageProvider


@lru_cache
def get_chat_provider() -> AIChatProvider:
    settings = get_settings()
    providers = {
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "groq": GroqProvider,
    }
    provider_cls = providers.get(settings.ai_chat_provider)
    if not provider_cls:
        raise ValueError(f"Unknown chat provider: {settings.ai_chat_provider}")
    return provider_cls()


@lru_cache
def get_image_provider() -> ImageGenerationProvider:
    settings = get_settings()
    providers = {
        "fal": FalProvider,
        "replicate": ReplicateProvider,
    }
    provider_cls = providers.get(settings.image_provider)
    if not provider_cls:
        raise ValueError(f"Unknown image provider: {settings.image_provider}")
    return provider_cls()


@lru_cache
def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    providers = {
        "minio": MinioStorageProvider,
        "s3": S3StorageProvider,
    }
    provider_cls = providers.get(settings.storage_provider)
    if not provider_cls:
        raise ValueError(f"Unknown storage provider: {settings.storage_provider}")
    return provider_cls()
