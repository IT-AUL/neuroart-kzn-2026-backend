import json
import logging
import re
from typing import List, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.db.models.location import Location
from app.schemas.ai import (
    AIChatResponse,
    ChatMessage,
    GenerateLocationContentResponse,
    LocationContentVariant,
)

logger = logging.getLogger(__name__)

FOUNDATION_MODELS_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
OPENAI_COMPATIBLE_API_URL = "https://ai.api.cloud.yandex.net/v1/chat/completions"


class YandexLLMService:
    def __init__(self):
        self.api_key = settings.YANDEX_GPT_API_KEY
        self.folder_id = settings.YANDEX_GPT_FOLDER_ID
        self.model_uri = settings.resolved_model_uri
        self.temperature = settings.YANDEX_GPT_TEMPERATURE
        self.max_tokens = settings.YANDEX_GPT_MAX_TOKENS

    def _build_system_prompt(self, location: Location) -> str:
        texts = location.texts or {}
        layer1 = texts.get("layer1", "")
        layer2 = texts.get("layer2", "")

        return (
            f"Ты — виртуальный фольклорный гид по интерактивному маршруту Казани 'NeuroArt KZN 2026'.\n"
            f"Текущая точка маршрута: '{location.title}' (ID: {location.id}).\n"
            f"Механика квеста на точке: {location.mechanic}.\n"
            f"Факты и предыстория этой точки:\n"
            f"- Основной факт: {layer1}\n"
            f"- Историко-культурный контекст и пасхалки: {layer2}\n\n"
            f"Твоя задача — отвечать туристу доброжелательно, колоритно, передавая дух татарских традиций, "
            f"фольклора и истории. Можешь давать подсказки по механике точки или рассказывать интересные "
            f"детали легенды. Отвечай на русском языке."
        )

    async def _call_openai_compatible_api(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """Calls Yandex Cloud AI Studio OpenAI-compatible chat completions endpoint."""
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.text})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model_uri,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        # Endpoints for Yandex Cloud OpenAI-compatible API
        endpoints_to_try = [
            "https://llm.api.cloud.yandex.net/v1/chat/completions",
            OPENAI_COMPATIBLE_API_URL,
        ]

        last_error = None
        for endpoint in endpoints_to_try:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(endpoint, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "")
                    else:
                        last_error = f"{endpoint} status {response.status_code}: {response.text}"
            except Exception as e:
                last_error = str(e)

        raise LLMServiceError(f"OpenAI-compatible API failed: {last_error}")

    async def _call_foundation_models_api(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """Calls standard Yandex Foundation Models completion endpoint."""
        messages = [{"role": "system", "text": system_prompt}]
        if history:
            for msg in history:
                messages.append({"role": msg.role, "text": msg.text})
        messages.append({"role": "user", "text": user_prompt})

        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": self.temperature,
                "maxTokens": str(self.max_tokens),
            },
            "messages": messages,
        }

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                FOUNDATION_MODELS_API_URL,
                json=payload,
                headers=headers,
            )
            if response.status_code != 200:
                # If error asks to use OpenAI API, raise specific error to trigger fallback
                raise LLMServiceError(response.text)

            data = response.json()
            alternatives = data.get("result", {}).get("alternatives", [])
            if not alternatives:
                raise LLMServiceError("No text alternatives returned by YandexGPT")

            return alternatives[0].get("message", {}).get("text", "")

    async def chat_about_location(
        self,
        location: Location,
        user_prompt: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> AIChatResponse:
        system_prompt = self._build_system_prompt(location)

        if not settings.is_gpt_configured:
            # Fallback mock response for development / demo without active cloud credentials
            mock_reply = (
                f"[Демо-режим YandexGPT] Приветствую на точке «{location.title}»! "
                f"Вы спросили: «{user_prompt}». "
                f"Знаете ли вы, что: {location.texts.get('layer1', '')} "
                f"А еще: {location.texts.get('layer2', '')}"
            )
            return AIChatResponse(
                location_id=location.id,
                location_title=location.title,
                answer=mock_reply,
                model="yandexgpt-demo-fallback",
                is_mock=True,
            )

        # If model URI indicates an Alice model or user specified, prioritize OpenAI-compatible API
        is_alice_or_openai = "aliceai" in self.model_uri or "openai" in self.model_uri

        answer_text = ""
        if is_alice_or_openai:
            answer_text = await self._call_openai_compatible_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                history=history,
            )
        else:
            try:
                answer_text = await self._call_foundation_models_api(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    history=history,
                )
            except LLMServiceError as e:
                # If Yandex returned "Please use HTTP OpenAI API instead", automatically retry with OpenAI endpoint
                if "OpenAI API" in str(e):
                    logger.info("Retrying with Yandex OpenAI-compatible API endpoint...")
                    answer_text = await self._call_openai_compatible_api(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        history=history,
                    )
                else:
                    raise

        return AIChatResponse(
            location_id=location.id,
            location_title=location.title,
            answer=answer_text,
            model=self.model_uri,
            is_mock=False,
        )

    def _get_mock_variants(
        self,
        title: str,
        context: Optional[str],
        count: int,
    ) -> List[LocationContentVariant]:
        theme = context or "татарская легенда и городская традиция Казани"
        variants: List[LocationContentVariant] = []

        v1 = LocationContentVariant(
            variant_id="variant_1_classic",
            layer1=f"Историческое место Казани, посвящённое теме «{title}»: вековые традиции, ремесло и гостеприимство.",
            layer2=f"С этим уголком связана старинная легенда: {theme}. Предания гласят, что здесь переплетаются духи природы и мудрость древних батыров.",
            action_hint=f"Исследуйте интерактивную AR-сцену «{title}» и проведите пальцем по контуру главного символа.",
            dialogue=[
                {
                    "speaker": "Старец-сказитель",
                    "text": f"Добро пожаловать к «{title}»! Вглядись в детали этой сказки.",
                    "trigger": "enter",
                },
                {
                    "speaker": "Герой",
                    "text": "Где сила не справится, там народная мудрость выручит!",
                    "trigger": "complete",
                },
            ],
            easter_egg=f"Старинная пословица: всякий путник на казанской земле обретает силу, если уважает традиции предков.",
            artifact_suggestion={
                "id": "relic_symbol",
                "name": f"Символ: {title[:20]}",
                "icon": "icons/symbol.png",
            },
        )
        variants.append(v1)

        if count > 1:
            v2 = LocationContentVariant(
                variant_id="variant_2_mythological",
                layer1=f"Оживлённый фольклорный образ Казани вокруг сюжета «{title}», знакомый каждому с детства.",
                layer2=f"В народных преданиях здесь обитают загадочные лесные и водные духи. Главный мотив — испытание на честность и доброе сердце.",
                action_hint=f"Тапните по ключевому объекту сцены, чтобы разгадать загадку локации.",
                dialogue=[
                    {
                        "speaker": "Хранитель места",
                        "text": f"Испытай свою удачу и сноровку на точке «{title}»!",
                        "trigger": "start",
                    }
                ],
                easter_egg="Шуточный секрет: если улыбнуться и трижды коснуться маркера, духи помогут в пути.",
                artifact_suggestion={
                    "id": "talisman_amulet",
                    "name": "Оберег батыра",
                    "icon": "icons/amulet.png",
                },
            )
            variants.append(v2)

        if count > 2:
            v3 = LocationContentVariant(
                variant_id="variant_3_interactive",
                layer1=f"Культурный символ Казани, где каждый камень и поворот хранит тепло татарского гостеприимства.",
                layer2=f"Здесь воспевается трудолюбие и единство народа: от праздников Сабантуя до тихих вечеров за самоваром.",
                action_hint=f"Соберите коллекционный сувенир, выполнив быстрое действие на экране.",
                dialogue=[
                    {
                        "speaker": "Хозяин майдана",
                        "text": "Рәхим итегез! Гостям всегда рады на нашей земле!",
                        "trigger": "start",
                    }
                ],
                easter_egg="Народная мудрость: сытый гость — радость в доме, а весёлый путник — добрый знак.",
                artifact_suggestion={
                    "id": "gift_chak",
                    "name": "Праздничный подарок",
                    "icon": "icons/gift.png",
                },
            )
            variants.append(v3)

        return variants[:count]

    async def generate_location_variants(
        self,
        title: str,
        context: Optional[str] = None,
        count: int = 2,
    ) -> GenerateLocationContentResponse:
        if not settings.is_gpt_configured:
            return GenerateLocationContentResponse(
                title=title,
                options=self._get_mock_variants(title, context, count),
                model="yandexgpt-demo-fallback",
                is_mock=True,
            )

        system_prompt = (
            "Ты — фольклорист и креативный сценарист интерактивного туристического AR-квеста по Казани «NeuroArt KZN 2026».\n"
            f"Создай ровно {count} разных вариантов текстов для точки маршрута в строгом формате JSON.\n"
            "Каждый вариант должен содержать следующие поля:\n"
            "- variant_id: уникальная строка (например 'variant_1')\n"
            "- layer1: бытовой / прикладной факт (1-2 предложения)\n"
            "- layer2: историко-культурный или мифологический контекст (2-3 предложения)\n"
            "- action_hint: инструкция игроку, что делать в AR-сцене\n"
            "- dialogue: список объектов [{'speaker': '...', 'text': '...', 'trigger': '...'}]\n"
            "- easter_egg: фольклорная шутка, пословица или пасхалка\n"
            "- artifact_suggestion: объект {'id': '...', 'name': '...', 'icon': 'icons/...'}\n\n"
            "Ответ должен быть ТОЛЬКО валидным JSON-массивом из объектов, без обертки в markdown ```json."
        )

        user_prompt = f"Название точки: «{title}».\nКонтекст/тема: {context or 'фольклор и традиции Казани'}."

        try:
            raw_text = ""
            is_alice_or_openai = "aliceai" in self.model_uri or "openai" in self.model_uri
            if is_alice_or_openai:
                raw_text = await self._call_openai_compatible_api(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            else:
                raw_text = await self._call_foundation_models_api(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )

            # Strip markdown formatting if any
            cleaned_text = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.IGNORECASE)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text.strip())

            parsed = json.loads(cleaned_text)
            if isinstance(parsed, list):
                variants = [LocationContentVariant(**item) for item in parsed]
                return GenerateLocationContentResponse(
                    title=title,
                    options=variants[:count],
                    model=self.model_uri,
                    is_mock=False,
                )
        except Exception as e:
            logger.warning("LLM structured generation failed (%s), using intelligent fallback", e)

        # Fallback to rich template mock
        return GenerateLocationContentResponse(
            title=title,
            options=self._get_mock_variants(title, context, count),
            model="yandexgpt-fallback-template",
            is_mock=True,
        )


yandex_llm_service = YandexLLMService()

