# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Обзор проекта

Бэкенд на FastAPI для «NeuroArt KZN 2026» — интерактивного туристического AR-маршрута по Казани. Отдает конфигурации точек маршрута (`Location`: 3D-модели, анимации, тексты, параметры механик), валидирует телеметрию AR мини-игр на сервере, ведет сессионный прогресс/паспорт, интегрируется с Yandex Cloud S3 и YandexGPT, а также включает парсер POI из OSM + рекомендатель для редактора квестов с панелью HITL-модерации.

Полная архитектура, модель данных и спецификация API описаны в [DOCUMENTATION.md](DOCUMENTATION.md) и [README.md](README.md) — при необходимости деталей по эндпоинтам/схемам сверяйся с ними, а не восстанавливай их из исходников заново.

## Команды

```bash
uv sync                                          # установка зависимостей
uv run uvicorn app.main:app --reload --port 8000 # запуск dev-сервера (Swagger на /docs, админка на /admin)
uv run pytest -v                                 # запуск всех тестов
uv run pytest tests/test_mechanics.py -v         # запуск одного файла тестов
uv run pytest tests/test_mechanics.py::test_name -v  # запуск одного теста
docker compose up --build -d                     # запуск через Docker

# Боевые интеграционные/демо-скрипты (ходят в реальный Yandex Cloud / OSM Overpass — нужен настроенный .env)
uv run python scripts/verify_yandex_integrations.py
uv run python scripts/verify_poi_tagging_live.py
uv run python scripts/demo_editor_flow.py

# Запуск модуля POI как автономного микросервиса на отдельном порту
uv run python -m app.services.poi.standalone --port 8001
```

Линтер/форматтер в репозитории не настроены.

Конфигурация берется из `.env` (шаблон — `.env.example`), загружается через `app/core/config.py` (`pydantic-settings`). Тестам `.env` не нужен — они работают против in-memory SQLite.

## Архитектура

**Слои**: `app/api/v1/*` (роуты) → `app/services/*` (бизнес-логика) → `app/db/models/*` (SQLAlchemy ORM). Pydantic-схемы в `app/schemas/*` — это контракты запросов/ответов, намеренно отделенные от ORM-моделей. Каждый роут в `api_v1_router` (`app/api/v1/router.py`) монтируется в `app/main.py` дважды: один раз в корне (`/locations`, `/progress`, ...) и один раз с префиксом `/api/v1` — при изменении роутов следи, чтобы оба варианта продолжали работать.

**Сессии, а не авторизация**: логина нет. Клиент сам генерирует UUID и передает его как `X-Session-ID` в каждом запросе к прогрессу/паспорту. `app/api/deps.py::get_session_id` извлекает и валидирует этот заголовок; весь прогресс и паспорт привязаны только к этому session ID, без какой-либо другой проверки идентичности.

**Движок валидации механик** (`app/services/mechanics/`): у каждого типа AR мини-игры (`trace`, `tap_climb`, `tap_strike`, `none`) свой валидатор, реализующий `BaseMechanicValidator.validate(mechanic_params, submission_data) -> MechanicValidationResult` (`base.py`). `tap_climb` симулирует физику затухания/прироста по таймстемпам тапов (либо по числу тапов и длительности); `trace` проверяет расстояние от точек пользователя до отрезков эталонного контура в пределах пиксельного `tolerance`. `POST /progress/{location_id}` запускает нужный валидатор и открывает артефакт только при успехе (иначе `422`); `POST /progress/verify/{location_id}` выполняет ту же валидацию без сохранения — используй этот эндпоинт для подбора параметров механики без изменения паспорта.

**Идемпотентность прогресса**: повторная отправка уже пройденной точки не дублирует артефакт в паспорте — возвращается `is_new_unlock: false` с датой первого открытия. Эта логика — в `app/services/passport_service.py`.

**Авто-миграция SQLite при старте**: `app/main.py::_sync_sqlite_migrate` при старте lifespan делает `PRAGMA table_info` по таблице `locations` и добавляет через `ALTER TABLE ... ADD COLUMN` любые отсутствующие колонки (например `models`, `next_location_id`). Alembic-миграций нет — при добавлении новой колонки в `Location` нужно добавить соответствующий условный `ALTER TABLE` сюда, иначе старые файлы SQLite-базы перестанут открываться.

**Сидинг**: `app/db/seeds/seeder.py::seed_locations` идемпотентно вставляет 3 фиксированные демо-точки из `initial_data.py` при каждом старте (и в фикстуре тестов `conftest.py`). Данные POI засеваются из OSM один раз при первом старте, если таблица `pois` пуста (см. lifespan в `app/main.py`), после чего автоматически помечаются `approved` для демо.

**Пайплайн POI** (`app/services/poi/`): `osm_client.py` тянет данные из Overpass API (с встроенным резервным датасетом на случай недоступности Overpass) → `tag_engine.py` делает двухуровневое авто-тегирование (6 значений `category`, 6 семантических `tags`) → результат попадает в таблицу `pois` со статусом `pending`, ожидая модерации через `GET /poi/admin/pending` / `POST /poi/admin/{id}/review`. `sync_manager.py` пересинхронизирует данные из OSM, сохраняя правки куратора (не перезатирает категорию/теги у уже `approved`/`rejected` POI). `recommender.py` скорит POI по дистанции Хаверсина + совпадению тегов/категории для `GET /poi/recommendations`. `POST /locations/from-poi` напрямую конвертирует подтвержденный POI в играбельную `Location`.

**HITL-генерация контента**: `app/services/yandex_llm_service.py` оборачивает оба протокола вызова YandexGPT (OpenAI-совместимый `/v1/chat/completions` и нативный Foundation Models `/foundationModels/v1/completion`). Если API-ключ не настроен, вместо ошибки используется детерминированный мок-ответ («фольклорная заглушка») — это отражается полем `is_mock` в ответе. `POST /locations/editor/generate-content` генерирует черновой текст точки через LLM; человек выбирает/правит вариант и вызывает `POST /locations/{id}/editor/approve-content`, чтобы сохранить его — LLM никогда не пишет в БД напрямую.

**Админ-панель** (`app/admin/router.py` + `app/templates/`): server-rendered Jinja2 SSR (не SPA) на `/admin`, покрывает CRUD квестов, модерацию POI и синхронизацию с OSM — отделена от JSON API и не версионируется под `/api/v1`.

**Резолв URL хранилища**: `Location.models[].url` / `model_url` хранятся как относительные ключи (например `models/foo.glb`); `app/services/location_service.py` превращает их в абсолютные ссылки через `YANDEX_S3_PUBLIC_BASE_URL`, если она задана. Не хардкодь базовый URL S3 в других местах.

## Заметки про тесты

Тесты используют `pytest-asyncio` в режиме `auto` (см. `pytest.ini`) — `@pytest.mark.asyncio` не нужен. `tests/conftest.py` подменяет `get_db` на in-memory SQLite, пересоздает все таблицы и заново засевает локации перед каждым тестом (`autouse`-фикстура), поэтому тесты изолированы друг от друга и от реального `.env`/файла БД. Для тестов эндпоинтов используй фикстуру `client` (`httpx.AsyncClient` поверх приложения).
