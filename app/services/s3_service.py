import logging
from typing import Optional
import aioboto3
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.exceptions import S3ServiceError
from app.schemas.storage import (
    S3PresignedUploadResponse,
    S3PresignedUrlResponse,
    S3StatusResponse,
    S3UploadResponse,
)

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.endpoint_url = settings.YANDEX_S3_ENDPOINT_URL
        self.bucket_name = settings.YANDEX_S3_BUCKET_NAME
        self.access_key = settings.YANDEX_S3_ACCESS_KEY_ID
        self.secret_key = settings.YANDEX_S3_SECRET_ACCESS_KEY
        self.region_name = settings.YANDEX_S3_REGION_NAME
        self.session = aioboto3.Session()

    def _get_client_context(self):
        return self.session.client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
        )

    async def check_status(self) -> S3StatusResponse:
        if not settings.is_s3_configured:
            return S3StatusResponse(
                configured=False,
                bucket=self.bucket_name,
                endpoint=self.endpoint_url,
                region=self.region_name,
                accessible=False,
                message="Yandex S3 credentials are not configured in .env",
            )

        try:
            async with self._get_client_context() as s3:
                await s3.head_bucket(Bucket=self.bucket_name)
                return S3StatusResponse(
                    configured=True,
                    bucket=self.bucket_name,
                    endpoint=self.endpoint_url,
                    region=self.region_name,
                    accessible=True,
                    message="Connected to Yandex Object Storage successfully",
                )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            return S3StatusResponse(
                configured=True,
                bucket=self.bucket_name,
                endpoint=self.endpoint_url,
                region=self.region_name,
                accessible=False,
                message=f"S3 ClientError ({error_code}): {e}",
            )
        except Exception as e:
            return S3StatusResponse(
                configured=True,
                bucket=self.bucket_name,
                endpoint=self.endpoint_url,
                region=self.region_name,
                accessible=False,
                message=f"Failed to connect to Yandex S3: {str(e)}",
            )

    async def upload_bytes(
        self,
        file_bytes: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> S3UploadResponse:
        if not settings.is_s3_configured:
            # Fallback mock for local development / testing
            mock_url = f"{self.endpoint_url}/{self.bucket_name}/{key}"
            return S3UploadResponse(
                key=key,
                bucket=self.bucket_name,
                url=mock_url,
                size_bytes=len(file_bytes),
                content_type=content_type,
            )

        try:
            async with self._get_client_context() as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file_bytes,
                    ContentType=content_type,
                )
                url = f"{self.endpoint_url}/{self.bucket_name}/{key}"
                return S3UploadResponse(
                    key=key,
                    bucket=self.bucket_name,
                    url=url,
                    size_bytes=len(file_bytes),
                    content_type=content_type,
                )
        except Exception as e:
            logger.error("Failed to upload to Yandex S3: %s", e)
            raise S3ServiceError(message=str(e))

    async def generate_presigned_download_url(
        self,
        key: str,
        expires_in_seconds: int = 3600,
    ) -> S3PresignedUrlResponse:
        if not settings.is_s3_configured:
            mock_url = f"{self.endpoint_url}/{self.bucket_name}/{key}?mock_token=dev"
            return S3PresignedUrlResponse(
                key=key,
                download_url=mock_url,
                expires_in_seconds=expires_in_seconds,
            )

        try:
            async with self._get_client_context() as s3:
                url = await s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket_name, "Key": key},
                    ExpiresIn=expires_in_seconds,
                )
                return S3PresignedUrlResponse(
                    key=key,
                    download_url=url,
                    expires_in_seconds=expires_in_seconds,
                )
        except Exception as e:
            logger.error("Failed to generate presigned URL for Yandex S3: %s", e)
            raise S3ServiceError(message=str(e))

    async def generate_presigned_upload_url(
        self,
        key: str,
        content_type: str = "application/octet-stream",
        expires_in_seconds: int = 1800,
    ) -> S3PresignedUploadResponse:
        public_url = (
            f"{settings.YANDEX_S3_PUBLIC_BASE_URL.rstrip('/')}/{key.lstrip('/')}"
            if settings.YANDEX_S3_PUBLIC_BASE_URL
            else f"{self.endpoint_url}/{self.bucket_name}/{key}"
        )

        if not settings.is_s3_configured:
            mock_upload_url = f"{self.endpoint_url}/{self.bucket_name}/{key}?mock_upload=true"
            return S3PresignedUploadResponse(
                key=key,
                upload_url=mock_upload_url,
                public_url=public_url,
                method="PUT",
                content_type=content_type,
                expires_in_seconds=expires_in_seconds,
            )

        try:
            async with self._get_client_context() as s3:
                upload_url = await s3.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": key,
                        "ContentType": content_type,
                    },
                    ExpiresIn=expires_in_seconds,
                )
                return S3PresignedUploadResponse(
                    key=key,
                    upload_url=upload_url,
                    public_url=public_url,
                    method="PUT",
                    content_type=content_type,
                    expires_in_seconds=expires_in_seconds,
                )
        except Exception as e:
            logger.error("Failed to generate presigned upload URL for Yandex S3: %s", e)
            raise S3ServiceError(message=str(e))

    async def delete_object(self, key: str) -> bool:
        if not settings.is_s3_configured:
            return True

        try:
            async with self._get_client_context() as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=key)
                return True
        except Exception as e:
            logger.error("Failed to delete object from Yandex S3: %s", e)
            raise S3ServiceError(message=str(e))

    async def list_objects(self, prefix: str = "", limit: int = 100):
        """Lists objects stored in Yandex S3 bucket matching prefix."""
        if not settings.is_s3_configured:
            defaults = [
                {"key": "icons/comb.png", "size": 15420, "url": f"{self.endpoint_url}/{self.bucket_name}/icons/comb.png"},
                {"key": "icons/shurale.png", "size": 18200, "url": f"{self.endpoint_url}/{self.bucket_name}/icons/shurale.png"},
                {"key": "icons/chakchak.png", "size": 12100, "url": f"{self.endpoint_url}/{self.bucket_name}/icons/chakchak.png"},
                {"key": "markers/marker_log.png", "size": 45100, "url": f"{self.endpoint_url}/{self.bucket_name}/markers/marker_log.png"},
                {"key": "markers/marker_default.png", "size": 38200, "url": f"{self.endpoint_url}/{self.bucket_name}/markers/marker_default.png"},
                {"key": "models/loc1_log_shurale.glb", "size": 3200000, "url": f"{self.endpoint_url}/{self.bucket_name}/models/loc1_log_shurale.glb"},
            ]
            if prefix:
                return [d for d in defaults if d["key"].startswith(prefix)]
            return defaults

        try:
            async with self._get_client_context() as s3:
                resp = await s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix, MaxKeys=limit)
                contents = resp.get("Contents", [])
                base_url = settings.YANDEX_S3_PUBLIC_BASE_URL or f"{self.endpoint_url}/{self.bucket_name}"
                return [
                    {
                        "key": item["Key"],
                        "size": item["Size"],
                        "last_modified": item["LastModified"].isoformat() if item.get("LastModified") else None,
                        "url": f"{base_url.rstrip('/')}/{item['Key'].lstrip('/')}",
                    }
                    for item in contents
                ]
        except Exception as e:
            logger.error("Failed to list objects from Yandex S3: %s", e)
            return []


s3_service = S3Service()
