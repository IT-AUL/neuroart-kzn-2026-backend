import asyncio
import sys
import uuid
import httpx
from app.core.config import settings
from app.db.models.location import Location
from app.services.s3_service import s3_service


async def main():
    print("=" * 60, flush=True)
    print("NeuroArt KZN 2026 - Yandex Cloud Integration Verification", flush=True)
    print("=" * 60, flush=True)

    # -------------------------------------------------------------
    # 1. Check S3 Configuration and Connection
    # -------------------------------------------------------------
    print("\n[1/2] Testing Yandex Object Storage (S3)...", flush=True)
    status = await s3_service.check_status()
    if status.accessible:
        print(f"  [SUCCESS] Bucket '{settings.YANDEX_S3_BUCKET_NAME}' is accessible!", flush=True)
    else:
        print(f"  [FAILED] Cannot access bucket. Error: {status.message}", flush=True)

    # -------------------------------------------------------------
    # 2. Check Yandex LLM (YandexGPT)
    # -------------------------------------------------------------
    print("\n[2/2] Testing Yandex LLM...", flush=True)
    print(f"  [*] Current Model URI from config: {settings.resolved_model_uri}", flush=True)

    # Test A: OpenAI-compatible API endpoint
    print("  [*] Test A: Trying Yandex Cloud OpenAI-compatible API (https://llm.api.cloud.yandex.net/v1/chat/completions)...", flush=True)
    openai_payload = {
        "model": settings.resolved_model_uri,
        "messages": [
            {"role": "system", "content": "Ты дружелюбный гид по Казани."},
            {"role": "user", "content": "Поприветствуй гостя в 3 словах."},
        ],
        "temperature": 0.6,
        "max_tokens": 100,
    }

    openai_headers_options = [
        {"Authorization": f"Api-Key {settings.YANDEX_GPT_API_KEY}", "Content-Type": "application/json"},
        {"Authorization": f"Bearer {settings.YANDEX_GPT_API_KEY}", "Content-Type": "application/json"},
    ]

    openai_success = False
    for i, headers in enumerate(openai_headers_options, 1):
        auth_type = "Api-Key" if "Api-Key" in headers["Authorization"] else "Bearer"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://llm.api.cloud.yandex.net/v1/chat/completions",
                    json=openai_payload,
                    headers=headers,
                )
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"  [SUCCESS] OpenAI API (auth: {auth_type}) answered:", flush=True)
                    print(f"            \"{answer.strip()}\"", flush=True)
                    openai_success = True
                    break
                else:
                    print(f"  [INFO] OpenAI API ({auth_type}) returned status {res.status_code}: {res.text[:180]}", flush=True)
        except Exception as e:
            print(f"  [INFO] OpenAI API ({auth_type}) error: {e}", flush=True)

    # Test B: Foundation Models API (native YandexGPT)
    print("\n  [*] Test B: Trying native Foundation Models API (yandexgpt/latest)...", flush=True)
    standard_model_uri = f"gpt://{settings.YANDEX_GPT_FOLDER_ID}/yandexgpt/latest"
    print(f"      Model URI: {standard_model_uri}", flush=True)
    foundation_payload = {
        "modelUri": standard_model_uri,
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "100",
        },
        "messages": [
            {"role": "system", "text": "Ты гид по Казани."},
            {"role": "user", "text": "Поприветствуй гостя в 3 словах."},
        ],
    }
    foundation_headers = {
        "Authorization": f"Api-Key {settings.YANDEX_GPT_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                json=foundation_payload,
                headers=foundation_headers,
            )
            if res.status_code == 200:
                data = res.json()
                alt = data.get("result", {}).get("alternatives", [{}])[0]
                text = alt.get("message", {}).get("text", "")
                print(f"  [SUCCESS] Native Foundation Models API answered:", flush=True)
                print(f"            \"{text.strip()}\"", flush=True)
            else:
                print(f"  [INFO] Foundation Models API returned status {res.status_code}: {res.text[:180]}", flush=True)
    except Exception as e:
        print(f"  [INFO] Foundation Models API error: {e}", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("Verification complete.", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
