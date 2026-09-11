from typing import Optional
from pydantic import BaseModel


class S3UploadResponse(BaseModel):
    key: str
    bucket: str
    url: str
    size_bytes: int
    content_type: str


class S3PresignedUrlResponse(BaseModel):
    key: str
    download_url: str
    expires_in_seconds: int


class S3StatusResponse(BaseModel):
    configured: bool
    bucket: str
    endpoint: str
    region: str
    accessible: bool
    message: str


class S3PresignedUploadRequest(BaseModel):
    filename: str
    content_type: str = "model/gltf-binary"
    key_prefix: str = "models"
    expires_in_seconds: int = 1800


class S3PresignedUploadResponse(BaseModel):
    key: str
    upload_url: str
    public_url: str
    method: str = "PUT"
    content_type: str
    expires_in_seconds: int

