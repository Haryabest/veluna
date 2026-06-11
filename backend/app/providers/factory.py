from functools import lru_cache

from app.core.config import get_settings
from app.providers.ai.base import AIChatProvider
from app.providers.ai.chat_providers import GroqProvider, OpenAIProvider, OpenRouterProvider
from app.providers.ai.genapi_provider import GenApiProvider
from app.providers.ai.stub_provider import StubChatProvider
from app.providers.ai.image_base import ImageGenerationProvider
from app.providers.ai.image_providers import CivitaiProvider, FalProvider, ReplicateProvider
from app.providers.ai.zimage_provider import ZImageProvider
from app.providers.storage.base import StorageProvider
from app.providers.storage.providers import MinioStorageProvider, S3StorageProvider


def _provider_has_key(settings, name: str) -> bool:
    if name == "genapi":
        return bool(settings.gen_api_key.strip())
    if name == "openai":
        return bool(settings.openai_api_key.strip())
    if name == "openrouter":
        return bool(settings.openrouter_api_key.strip())
    if name == "groq":
        return bool(settings.groq_api_key.strip())
    return False


@lru_cache
def get_chat_provider() -> AIChatProvider:
    settings = get_settings()
    providers = {
        "genapi": GenApiProvider,
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "groq": GroqProvider,
    }
    preferred = settings.ai_chat_provider
    if _provider_has_key(settings, preferred):
        return providers[preferred]()
    for name in ("genapi", "groq", "openrouter", "openai"):
        if name != preferred and _provider_has_key(settings, name):
            return providers[name]()
    return StubChatProvider()


def _image_provider_has_key(settings, name: str) -> bool:
    if name == "fal":
        return bool(settings.fal_api_key.strip())
    if name == "replicate":
        return bool(settings.replicate_api_token.strip())
    if name == "civitai":
        return bool(settings.civitai_api_key.strip())
    if name == "zimage":
        return bool(settings.gen_api_key.strip())
    return False


@lru_cache
def get_image_provider() -> ImageGenerationProvider:
    settings = get_settings()
    providers = {
        "fal": FalProvider,
        "replicate": ReplicateProvider,
        "civitai": CivitaiProvider,
        "zimage": ZImageProvider,
    }
    preferred = settings.image_provider
    if _image_provider_has_key(settings, preferred):
        return providers[preferred]()
    for name in ("zimage", "civitai", "fal", "replicate"):
        if name != preferred and _image_provider_has_key(settings, name):
            return providers[name]()
    provider_cls = providers.get(preferred)
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
