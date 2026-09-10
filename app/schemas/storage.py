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
