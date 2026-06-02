import io
from datetime import timedelta

import boto3
from botocore.config import Config
from minio import Minio

from app.core.config import get_settings
from app.providers.storage.base import (
    PresignedUrlResult,
    StorageBucket,
    StorageProvider,
    UploadResult,
)


class MinioStorageProvider(StorageProvider):
    def __init__(self):
        settings = get_settings()
        self._bucket = settings.minio_bucket
        self._public_url = settings.minio_public_url.rstrip("/")
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )

    @property
    def provider_name(self) -> str:
        return "minio"

    def _full_key(self, bucket: StorageBucket, key: str) -> str:
        return f"{bucket.value}/{key}"

    async def upload(self, bucket: StorageBucket, key: str, data: bytes, content_type: str) -> UploadResult:
        full_key = self._full_key(bucket, key)
        self._client.put_object(
            self._bucket,
            full_key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return UploadResult(key=full_key, url=f"{self._public_url}/{full_key}", bucket=self._bucket)

    async def delete(self, bucket: StorageBucket, key: str) -> bool:
        full_key = self._full_key(bucket, key)
        self._client.remove_object(self._bucket, full_key)
        return True

    async def get_presigned_url(self, bucket: StorageBucket, key: str, expires: int = 3600) -> PresignedUrlResult:
        full_key = self._full_key(bucket, key)
        url = self._client.presigned_get_object(
            self._bucket,
            full_key,
            expires=timedelta(seconds=expires),
        )
        return PresignedUrlResult(url=url, expires_in=expires, key=full_key)

    async def get_presigned_upload_url(
        self,
        bucket: StorageBucket,
        key: str,
        content_type: str = "image/jpeg",
        expires: int = 3600,
    ) -> PresignedUrlResult:
        full_key = self._full_key(bucket, key)
        url = self._client.presigned_put_object(
            self._bucket,
            full_key,
            expires=timedelta(seconds=expires),
        )
        public = f"{self._public_url}/{full_key}"
        return PresignedUrlResult(url=url, expires_in=expires, key=full_key, public_url=public)

    async def get_public_url(self, bucket: StorageBucket, key: str) -> str:
        return f"{self._public_url}/{self._full_key(bucket, key)}"

    async def health_check(self) -> bool:
        try:
            self._client.bucket_exists(self._bucket)
            return True
        except Exception:
            return False


class S3StorageProvider(StorageProvider):
    def __init__(self):
        settings = get_settings()
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(signature_version="s3v4"),
        )

    @property
    def provider_name(self) -> str:
        return "s3"

    def _full_key(self, bucket: StorageBucket, key: str) -> str:
        return f"{bucket.value}/{key}"

    async def upload(self, bucket: StorageBucket, key: str, data: bytes, content_type: str) -> UploadResult:
        full_key = self._full_key(bucket, key)
        self._client.put_object(
            Bucket=self._bucket,
            Key=full_key,
            Body=data,
            ContentType=content_type,
        )
        url = f"https://{self._bucket}.s3.amazonaws.com/{full_key}"
        return UploadResult(key=full_key, url=url, bucket=self._bucket)

    async def delete(self, bucket: StorageBucket, key: str) -> bool:
        full_key = self._full_key(bucket, key)
        self._client.delete_object(Bucket=self._bucket, Key=full_key)
        return True

    async def get_presigned_url(self, bucket: StorageBucket, key: str, expires: int = 3600) -> PresignedUrlResult:
        full_key = self._full_key(bucket, key)
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": full_key},
            ExpiresIn=expires,
        )
        return PresignedUrlResult(url=url, expires_in=expires, key=full_key)

    async def get_presigned_upload_url(
        self,
        bucket: StorageBucket,
        key: str,
        content_type: str = "image/jpeg",
        expires: int = 3600,
    ) -> PresignedUrlResult:
        full_key = self._full_key(bucket, key)
        url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": full_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires,
        )
        public = f"https://{self._bucket}.s3.amazonaws.com/{full_key}"
        return PresignedUrlResult(url=url, expires_in=expires, key=full_key, public_url=public)

    async def get_public_url(self, bucket: StorageBucket, key: str) -> str:
        return f"https://{self._bucket}.s3.amazonaws.com/{self._full_key(bucket, key)}"

    async def health_check(self) -> bool:
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return True
        except Exception:
            return False
