import uuid
import pytest
from app.core.config import settings
from app.db.models.location import Location
from app.services.s3_service import s3_service
from app.services.yandex_llm_service import yandex_llm_service


@pytest.mark.asyncio
async def test_live_s3_bucket_lifecycle():
    """
    Tests live S3 bucket operations:
    1. HeadBucket / connection check
    2. Upload test object
    3. Generate presigned URL
    4. Delete test object
    """
    if not settings.is_s3_configured:
        pytest.skip("Yandex S3 credentials are not configured in .env")

    # 1. Check bucket access
    status = await s3_service.check_status()
    assert status.accessible is True, f"Bucket not accessible: {status.message}"

    # 2. Upload test object
    test_key = f"test_verification/test_{uuid.uuid4().hex[:8]}.txt"
    payload = b"Live integration test payload"
    upload_res = await s3_service.upload_bytes(
        file_bytes=payload,
        key=test_key,
        content_type="text/plain",
    )
    assert upload_res.key == test_key
    assert upload_res.size_bytes == len(payload)

    # 3. Presigned URL
    presign_res = await s3_service.generate_presigned_download_url(key=test_key, expires_in_seconds=300)
    assert presign_res.download_url.startswith("http")

    # 4. Cleanup / Delete object
    delete_res = await s3_service.delete_object(key=test_key)
    assert delete_res is True


@pytest.mark.asyncio
async def test_live_yandex_gpt_completion():
    """
    Tests live YandexGPT completion using configured credentials.
    """
    if not settings.is_gpt_configured:
        pytest.skip("YandexGPT credentials are not configured in .env")

    test_location = Location(
        id="loc_test_kazan",
        title="Тестовая точка: Казанский Кремль",
        mechanic="none",
        texts={
            "layer1": "Казанский Кремль — главная достопримечательность столицы Татарстана.",
            "layer2": "Внесен в список всемирного наследия ЮНЕСКО в 2000 году.",
        },
    )

    response = await yandex_llm_service.chat_about_location(
        location=test_location,
        user_prompt="Скажи кратко одну интересную деталь о Казанском Кремле.",
    )

    assert response.is_mock is False, "YandexGPT fell back to mock mode, live API failed or not active"
    assert len(response.answer.strip()) > 10
    assert response.model is not None
