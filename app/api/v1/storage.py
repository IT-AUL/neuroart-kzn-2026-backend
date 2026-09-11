from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import RedirectResponse
from app.schemas.storage import (
    S3PresignedUploadRequest,
    S3PresignedUploadResponse,
    S3PresignedUrlResponse,
    S3StatusResponse,
    S3UploadResponse,
)
from app.services.s3_service import s3_service

router = APIRouter(prefix="/storage", tags=["Yandex Object Storage (S3)"])


@router.get(
    "/status",
    response_model=S3StatusResponse,
    summary="Check Yandex Cloud Object Storage connection status",
)
async def get_storage_status() -> S3StatusResponse:
    return await s3_service.check_status()


@router.get(
    "/files",
    summary="List files and assets stored in Yandex S3 bucket",
    description="Returns files in bucket optionally filtered by folder prefix (e.g. 'models', 'markers', 'icons')",
)
async def list_storage_files(
    prefix: str = Query("", description="Folder or key prefix, e.g. 'icons' or 'models'"),
    limit: int = Query(100, ge=1, le=500),
):
    return await s3_service.list_objects(prefix=prefix, limit=limit)


@router.get(
    "/asset/{key:path}",
    summary="Directly view or download an asset image/model via presigned redirect",
)
async def view_asset_file(key: str):
    presigned = await s3_service.generate_presigned_download_url(key=key, expires_in_seconds=3600)
    return RedirectResponse(url=presigned.download_url, status_code=307)


@router.post(
    "/presign-upload",
    response_model=S3PresignedUploadResponse,
    summary="Generate presigned upload URL for direct client S3 upload with progress bar",
    description=(
        "Generates a pre-signed PUT URL directly to Yandex Object Storage. "
        "Allows frontend/editor UI to upload large 3D models or textures directly to S3 "
        "using XMLHttpRequest / axios with native onUploadProgress bar, bypassing the backend server."
    ),
)
async def get_presigned_upload_url(
    payload: S3PresignedUploadRequest,
) -> S3PresignedUploadResponse:
    key = f"{payload.key_prefix.strip('/')}/{payload.filename}"
    return await s3_service.generate_presigned_upload_url(
        key=key,
        content_type=payload.content_type,
        expires_in_seconds=payload.expires_in_seconds,
    )


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
