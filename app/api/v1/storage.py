from fastapi import APIRouter, File, Form, Query, UploadFile
from app.schemas.storage import S3PresignedUrlResponse, S3StatusResponse, S3UploadResponse
from app.services.s3_service import s3_service

router = APIRouter(prefix="/storage", tags=["Yandex Object Storage (S3)"])


@router.get(
    "/status",
    response_model=S3StatusResponse,
    summary="Check Yandex Cloud Object Storage connection status",
)
async def get_storage_status() -> S3StatusResponse:
    return await s3_service.check_status()


@router.post(
    "/upload",
    response_model=S3UploadResponse,
    summary="Upload an asset file (3D model, marker image, icon) to Yandex S3",
)
async def upload_asset(
    file: UploadFile = File(...),
    key_prefix: str = Form("assets", description="Prefix or folder in bucket"),
) -> S3UploadResponse:
    content = await file.read()
    key = f"{key_prefix.strip('/')}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"

    return await s3_service.upload_bytes(
        file_bytes=content,
        key=key,
        content_type=content_type,
    )


@router.get(
    "/presign/{key:path}",
    response_model=S3PresignedUrlResponse,
    summary="Generate presigned download URL for an S3 asset",
)
async def get_presigned_url(
    key: str,
    expires_in_seconds: int = Query(3600, ge=60, le=86400),
) -> S3PresignedUrlResponse:
    return await s3_service.generate_presigned_download_url(
        key=key,
        expires_in_seconds=expires_in_seconds,
    )


@router.delete(
    "/object/{key:path}",
    summary="Delete an object from Yandex S3 bucket",
)
async def delete_asset(key: str):
    await s3_service.delete_object(key=key)
    return {"status": "deleted", "key": key}
