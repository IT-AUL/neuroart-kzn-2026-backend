from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    PROJECT_NAME: str = "NeuroArt KZN 2026 Backend"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/neuroart.db"

    # Passport
    PASSPORT_TOTAL_SLOTS: int = 10

    # Yandex Object Storage (S3)
    YANDEX_S3_ENDPOINT_URL: str = "https://storage.yandexcloud.net"
    YANDEX_S3_BUCKET_NAME: str = "neuroart-kzn-assets"
    YANDEX_S3_ACCESS_KEY_ID: Optional[str] = None
    YANDEX_S3_SECRET_ACCESS_KEY: Optional[str] = None
    YANDEX_S3_REGION_NAME: str = "ru-central1"
    YANDEX_S3_PUBLIC_BASE_URL: Optional[str] = None

    # Yandex LLM (YandexGPT)
    YANDEX_GPT_API_KEY: Optional[str] = None
    YANDEX_GPT_FOLDER_ID: Optional[str] = None
    YANDEX_GPT_MODEL_URI: Optional[str] = None
    YANDEX_GPT_TEMPERATURE: float = 0.6
    YANDEX_GPT_MAX_TOKENS: int = 1000

    @property
    def is_s3_configured(self) -> bool:
        return bool(
            self.YANDEX_S3_ACCESS_KEY_ID
            and self.YANDEX_S3_SECRET_ACCESS_KEY
            and self.YANDEX_S3_BUCKET_NAME
        )

    @property
    def is_gpt_configured(self) -> bool:
        return bool(
            self.YANDEX_GPT_API_KEY
            and (self.YANDEX_GPT_FOLDER_ID or self.YANDEX_GPT_MODEL_URI)
        )

    @property
    def resolved_model_uri(self) -> str:
        if self.YANDEX_GPT_MODEL_URI:
            return self.YANDEX_GPT_MODEL_URI
        if self.YANDEX_GPT_FOLDER_ID:
            return f"gpt://{self.YANDEX_GPT_FOLDER_ID}/yandexgpt/latest"
        return "gpt://mock-folder/yandexgpt/latest"


settings = Settings()
