from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class StorageBucket(str, Enum):
    CHARACTERS = "characters"
    GENERATIONS = "generations"
    USERS = "users"
    PREVIEWS = "previews"


@dataclass
class UploadResult:
    key: str
    url: str
    bucket: str


@dataclass
class PresignedUrlResult:
    url: str
    expires_in: int


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, bucket: StorageBucket, key: str, data: bytes, content_type: str) -> UploadResult:
        pass

    @abstractmethod
    async def delete(self, bucket: StorageBucket, key: str) -> bool:
        pass

    @abstractmethod
    async def get_presigned_url(self, bucket: StorageBucket, key: str, expires: int = 3600) -> PresignedUrlResult:
        pass

    @abstractmethod
    async def get_public_url(self, bucket: StorageBucket, key: str) -> str:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
