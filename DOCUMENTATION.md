# Документация бекенда: NeuroArt KZN 2026

Интерактивный бэкенд-сервис для туристического AR-маршрута по Казани **«NeuroArt KZN 2026»**. 

Сервис отвечает за хранение и отдачу точек маршрута, параметров 3D-сцен и AR-механик, верификацию прохождения игровых механик, учет прогресса и выдачу трофеев в сессионный паспорт, а также интеграцию с **Yandex Cloud Object Storage (S3)** и **Yandex LLM (YandexGPT)**.

---

## 1. Стек технологий и архитектура

* **Язык и фреймворк**: Python 3.12+ / FastAPI (асинхронный REST API).
* **Менеджер пакетов и окружения**: `uv` (декларативное управление через `pyproject.toml` и `uv.lock`).
* **База данных**: SQLite в асинхронном режиме (`SQLAlchemy 2.0` async + `aiosqlite`).
* **Облачное хранилище**: Yandex Cloud Object Storage (S3-совместимый API на базе `aioboto3` и `boto3`).
* **Искусственный интеллект**: Yandex Cloud Foundation Models (YandexGPT и Alice AI через OpenAI-совместимый HTTP API и нативный API).
* **Контейнеризация**: Docker (multi-stage образ на базе `ghcr.io/astral-sh/uv`) + `docker-compose`.
* **Валидация и конфигурация**: `Pydantic v2` + `pydantic-settings` (загрузка конфигурации из файла `.env`).

### Структура проекта

```
neuroart-kzn-2026-backend/
├── app/
│   ├── api/
│   │   ├── deps.py                  # Извлечение и валидация X-Session-ID, внедрение сессий БД
│   │   └── v1/
│   │       ├── router.py            # Агрегатор маршрутов
│   │       ├── locations.py         # GET/POST /locations, POST /locations/from-poi
│   │       ├── progress.py          # POST /progress/{location_id}, POST /progress/verify/{id}
│   │       ├── passport.py          # GET /passport
│   │       ├── ai.py                # POST /locations/{id}/chat (YandexGPT гид)
│   │       ├── storage.py           # Статус S3, загрузка ассетов, presigned URL
│   │       └── poi.py               # Рекомендации точек, модерация (HITL), синхронизация OSM
│   ├── core/
│   │   ├── config.py                # Pydantic Settings конфигурация
│   │   ├── database.py              # Асинхронный движок SQLAlchemy и фабрика сессий
│   │   └── exceptions.py            # Кастомные HTTP-исключения
│   ├── db/
│   │   ├── base.py                  # Базовый класс моделей SQLAlchemy
│   │   ├── models/
│   │   │   ├── location.py          # ORM-модель точки маршрута с JSON-полями
│   │   │   ├── poi.py               # ORM-модели Poi и PoiSyncLog
│   │   │   └── progress.py          # ORM-модель прогресса сессии и трофеев
│   │   └── seeds/
│   │       ├── initial_data.py      # Фиксированные данные трех точек маршрута
│   │       └── seeder.py            # Идемпотентный сидер БД при старте сервиса
│   ├── schemas/
│   │   ├── location.py              # Схемы точек, координат, маркеров, параметров механик
│   │   ├── passport.py              # Схемы паспорта и собранных артефактов
│   │   ├── progress.py              # Схемы отправки телеметрии прохождения и ответа
│   │   ├── storage.py               # Схемы ответов S3
│   │   ├── ai.py                    # Схемы запросов и ответов диалога с LLM
│   │   └── poi.py                   # Схемы POI, рекомендаций, модерации и конвертации
│   ├── services/
│   │   ├── location_service.py      # Бизнес-логика точек и резолва URL моделей
│   │   ├── passport_service.py      # Учет прогресса, слоты паспорта, идемпотентность
│   │   ├── s3_service.py            # Клиент Yandex Object Storage (загрузка, presigned URL)
│   │   ├── yandex_llm_service.py    # Клиент YandexGPT (OpenAI-совместимый и нативный протоколы)
│   │   ├── poi/                     # Микросервис / модуль POI и рекомендаций
│   │   │   ├── osm_client.py        # Клиент Overpass API и резервный датасет Казани
│   │   │   ├── tag_engine.py        # Двухуровневая классификация и стемминг тегов
│   │   │   ├── sync_manager.py      # Синхронизация и защита кураторских правок
│   │   │   ├── recommender.py       # Пространственный (Haversine) и тематический скоринг
│   │   │   └── standalone.py        # Автономный раннер микросервиса (порт 8001)
│   │   └── mechanics/               # Движок валидации и физики игровых механик
│   │       ├── base.py              # Базовый интерфейс валидатора механик
│   │       ├── trace.py             # Геометрическая валидация обводки контура (trace)
│   │       ├── tap_climb.py         # Физическая симуляция лазания на столб (tap_climb)
│   │       ├── tap_strike.py        # Валидация механики тапа и удара (tap_strike)
│   │       └── none_mechanic.py     # Логика точек без мини-игры (none)
│   └── main.py                      # Точка входа, lifespan (авто-создание таблиц, сидинг POI и точек)
├── scripts/
│   ├── verify_yandex_integrations.py # Скрипт проверки боевого подключения к S3 и LLM
│   ├── verify_poi_tagging_live.py   # Скрипт боевой проверки парсинга OSM и разметки тегов
│   └── demo_editor_flow.py          # Сквозной тест сценария редактора квестов
├── tests/                           # Комплекс автоматических тестов (49 тестов)
├── .env.example                     # Шаблон переменных окружения
├── Dockerfile                       # Продакшн Dockerfile
├── docker-compose.yml               # Запуск сервиса в контейнере
├── pyproject.toml                   # Зависимости и метаданные проекта
└── pytest.ini                       # Настройки pytest
```


---

## 2. Модель данных: Точка маршрута (Location)

Каждая точка маршрута описывает интерактивную AR-сцену и содержит следующие поля:

| Поле | Тип | Описание |
|---|---|---|
| `id` | `string` | Уникальный строковый идентификатор точки (например, `loc_1_shurale`) |
| `order` | `integer` | Порядковый номер точки в маршруте (1, 2, 3...) |
| `priority` | `string` | Приоритет точки (`P0`, `P1`, `P2`) |
| `title` | `string` | Название точки |
| `mechanic` | `string` | Тип механики: `trace`, `tap_climb`, `tap_strike`, `none` |
| `mechanic_params` | `object` | Параметры механики (`path`, `tolerance`, `gain_per_tap`, `decay_interval_seconds`, `grace_period_seconds`, `success_threshold`) |
| `marker` | `object` | Тип маркера и имя файла ассета (`{ "type": "image", "asset": "marker_log.png" }`) |
| `model_url` | `string` | Основная 3D-модель сцены (`.glb`) для обратной совместимости |
| `models` | `array` | Список всех 3D-моделей сцены: `id`, `name`, `url`, `is_primary` |
| `coordinates` | `object` | Позиция и масштаб модели относительно маркера (`x`, `y`, `z`, `scale`) |
| `animations` | `array` | Список анимаций сцены: числовой `id` и строковое `name` |
| `texts` | `object` | Тексты и диалоги: `layer1`, `layer2`, `action_hint`, `dialogue`, `easter_egg` |
| `artifact` | `object` | Трофей для паспорта: `id`, `name`, `icon` (путь к иконке) |
| `next_location_id` | `string?` | ID следующей точки маршрута (или `null` для финала) |
| `next_location_order` | `integer?` | Порядковый номер следующей точки (или `null` для финала) |
| `next_location_hint` | `string?` | Подсказка игроку, куда двигаться дальше по маршруту |

---

### 2.1. Модель данных: Точка интереса POI (`Poi`) и лог синхронизации (`PoiSyncLog`)

Модель `pois` хранит распарсенные из OpenStreetMap и размеченные тегами объекты городской среды:

| Поле | Тип | Описание |
|---|---|---|
| `id` | `string` | Уникальный ID объекта (например, `poi_node_10000001`) |
| `osm_id` | `string` | Идентификатор OSM (`node/12345678` или `way/987654`) |
| `osm_type` | `string` | Тип геометрии в OSM (`node`, `way`, `relation`) |
| `name` | `string` | Основное название объекта (русское или локализованное) |
| `name_en` / `name_tt` | `string?` | Английское и татарское наименования (если доступны в OSM) |
| `latitude` / `longitude` | `float` | Географические координаты точки |
| `category` | `string` | Текущая подтвержденная категория (`monument`, `museum_culture`, `historic_quarter`, `nature_view`, `folklore_legends`, `architecture_heritage`) |
| `tags` | `array` | Список подтвержденных семантических тегов (`tatar_culture`, `unesco`, `ar_friendly`, `waterfront`, `photo_spot`, `family_friendly`) |
| `proposed_category` | `string?` | Категория, автоматически предложенная парсером |
| `proposed_tags` | `array` | Семантические теги, автоматически предложенные парсером |
| `raw_osm_tags` | `object` | Исходный JSON всех тегов из OpenStreetMap |
| `description` | `string?` | Историческая справка или выдержка из Википедии |
| `status` | `string` | Статус модерации: `pending` (ожидает проверки), `approved` (подтверждено), `rejected` |
| `confidence_score` | `float` | Оценка уверенности авто-разметки (0.0 — 1.0) |
| `admin_notes` | `string?` | Заметки модератора / куратора квестов |
| `last_synced_at` | `datetime` | Дата последнего обновления геометрии из OSM |

Таблица `poi_sync_logs` хранит историю периодических синхронизаций (`started_at`, `completed_at`, `status`, `points_scanned`, `points_created`, `points_updated`, `error_message`).

---

## 3. Точки маршрута и их наполнение


В сервис заложены 3 предустановленные точки:

### Точка 1: «Дровосек-батыр и Шурале» (`loc_1_shurale`)
* **Порядок / Приоритет**: `1` / `P0`
* **Механика**: `trace` (поддерживает телеметрию `hit_wedge: true` / `strike_performed: true`)
* **Параметры механики**:
  * `path`: контур для обводки пальцем (нормализованные координаты 0-1, либо плейсхолдер от 3D-художника).
  * `tolerance`: `20` (допустимое отклонение пальца от линии в пикселях).
* **Маркер**: `{"type": "image", "asset": "marker_log.png"}`
* **3D-модели (`models`)**:
  * `log_and_wedge` (основная, `is_primary: true`): `models/loc1_log_shurale.glb`
  * `shurale`: `models/loc1_shurale_char.glb`
  * `cart`: `models/loc1_cart.glb`
* **Координаты**: `{ "x": 0.0, "y": 0.0, "z": 0.0, "scale": 1.0 }`
* **Анимации** (8 состояний):
  0. `log_idle_crack_closed`
  1. `log_crack_open`
  2. `shurale_appear_threat`
  3. `shurale_idle`
  4. `shurale_insert_fingers`
  5. `wedge_hit`
  6. `shurale_trapped`
  7. `shurale_calls_for_help`
* **Тексты**:
  * `layer1`: «Одиночная работа в лесу была по-настоящему опасной, ценились смелость и смекалка.»
  * `layer2`: История поэмы Габдуллы Тукая (1907 г.), балета Фарида Яруллина, памятника у театра Камала.
  * `action_hint`: «Веди пальцем по щели бревна, затем тапни по клину для удара топором»
  * `dialogue`: реплики дровосека («Давай сперва вместе последнее бревно на телегу закинем...», «Где сила не может, там ум поможет»).
  * `easter_egg`: Шутка про имя «Вгодуминувшем» (Былтыр).
* **Навигация**: `next_location_id: "loc_2_sabantuy"`, `next_location_hint`: «Отправляйтесь на майдан на праздник Сабантуй к столбу с призом».
* **Артефакт**: `{ "id": "klin", "name": "Клин", "icon": "icons/klin.png" }`

---

### Точка 2: «Сабантуй, лазание на столб» (`loc_2_sabantuy`)
* **Порядок / Приоритет**: `2` / `P1`
* **Механика**: `tap_climb`
* **Параметры механики**:
  * `gain_per_tap`: `4.0` (прирост высоты за один тап).
  * `decay_per_interval`: `1.0` (соскальзывание вниз на 1 балл).
  * `decay_interval_seconds`: `0.3` (интервал соскальзывания — каждые 0.3 секунды).
  * `grace_period_seconds`: `1.0` (буфер паузы — соскальзывание включается только при паузе > 1 секунды).
  * `success_threshold`: `100.0` (порог победы, верхушка столба).
* **Маркер**: `{"type": "image", "asset": "marker_pole.png"}`
* **3D-модели (`models`)**:
  * `pole_and_towel` (основная, `is_primary: true`): `models/loc2_pole_climber.glb`
  * `climber`: `models/loc2_climber_char.glb`
* **Координаты**: `{ "x": 0.0, "y": 0.0, "z": 0.0, "scale": 1.0 }`
* **Анимации** (4 состояния):
  0. `climber_idle_base`
  1. `climbing_loop`
  2. `slip_down`
  3. `victory_grab_prize`
* **Тексты**:
  * `layer1`: «Сабантуй, праздник плуга, отмечает конец весеннего сева, один из главных праздников у татар и башкир.»
  * `layer2`: Традиции борьбы курэш, приз — живой баран, бег с ложкой и яйцом, разбивание горшка.
  * `action_hint`: «Лезь наверх, тапай часто, иначе соскользнешь! При паузе больше 1 секунды сползешь вниз.»
  * `dialogue`: реплика ведущего майдана.
  * `easter_egg`: Столб смазывают бараньим салом или мылом (высота 10-15 м), традиционный приз наверху — живой петух в клетке или узорные сапоги-ичиги.
* **Навигация**: `next_location_id: "loc_3_chak_chak"`, `next_location_hint`: «Загляните на праздничное чаепитие во дворе и угоститесь чак-чаком».
* **Артефакт**: `{ "id": "polotentse", "name": "Полотенце", "icon": "icons/polotentse.png" }`

---

### Точка 3: «Чаепитие и чак-чак» (`loc_3_chak_chak`)
* **Порядок / Приоритет**: `3` / `P2`
* **Механика**: `none`
* **Параметры механики**: `{}` (пустой объект).
* **Маркер**: `{"type": "image", "asset": "marker_table.png"}`
* **3D-модели (`models`)**:
  * `table_samovar` (основная, `is_primary: true`): `models/loc3_table_samovar.glb`
  * `chak_chak`: `models/loc3_chak_chak_dish.glb`
  * `cups`: `models/loc3_cups.glb`
* **Координаты**: `{ "x": 0.0, "y": 0.0, "z": 0.0, "scale": 1.0 }`
* **Анимации** (2 состояния):
  0. `samovar_steam_loop`
  1. `cup_fill`
* **Тексты**:
  * `layer1`: «Чак-чак как обязательное угощение на Сабантуе и главный символ татарского гостеприимства.»
  * `layer2`: Технология приготовления (тесто-жгутики, обжарка во фритюре, медовый сироп, горка на удачу), бренд «Вкусы России», музей чак-чака в Старо-Татарской слободе.
  * `action_hint`: «Здесь можно просто отдохнуть с дороги. Тапните по чак-чаку, чтобы положить угощение в альбом.»
  * `dialogue`: реплика хозяйки стола.
  * `easter_egg`: Легенда о происхождении чак-чака — угощение, испечённое матерью юноши взамен золотого выкупа хану Булгарии.
* **Навигация**: `next_location_id: null`, `next_location_hint`: «Поздравляем! Демо-маршрут завершен. Откройте экран альбома, чтобы увидеть собранные награды!».
* **Артефакт**: `{ "id": "chak_chak", "name": "Чак-чак", "icon": "icons/chak_chak.png" }`


---

## 4. Бизнес-логика игровых механик

В пакете [`app/services/mechanics/`](file:///c:/Users/galee/PycharmProjects/neuroart-kzn-2026-backend/app/services/mechanics/) реализована серверная валидация прохождения мини-игр.

### 4.1. Механика `tap_climb` (Лазание на столб)
Моделирует физику подъема персонажа по гладкому столбу:
* Каждую секунду персонаж соскальзывает со скоростью:
  $$\text{Decay Rate} = \frac{\text{decay\_per\_interval}}{\text{decay\_interval\_seconds}} = \frac{1.0}{0.3} \approx 3.33 \text{ очков/сек}$$
* Каждый тап дает $+4$ очка.
* Критическая частота тапов для движения вверх:
  $$\text{Min Rate} = \frac{3.33}{4.0} \approx 0.83 \text{ тапа/сек}$$
* **Способы валидации**:
  1. **По массиву таймстемпов (`tap_timestamps: [0.1, 0.25, 0.4...]`)**: пошаговое моделирование высоты в каждый момент времени. Проверяется, что пиковая высота достигла порога `100.0`.
  2. **По общему числу тапов и времени (`taps_count` и `duration_seconds`)**: расчет результирующей высоты с учетом общего затухания.
* **Результат**: при недостижении порога запрос отклоняется с кодом `422 Unprocessable Content` и подробным отчетом (например, `Climber fell down! Net score: 45.2/100`).

### 4.2. Механика `trace` (Обводка контура)
Геометрическая проверка точности обводки трещины в бревне:
* Принимает координаты точек, нарисованных пальцем пользователя (`user_path: [{"x": 0.1, "y": 0.2}, ...]`).
* Вычисляет минимальное перпендикулярное евклидово расстояние от каждой точки пальца до ближайшего отрезка эталонного контура.
* Если максимальное отклонение превышает `tolerance: 20px`, запрос отклоняется с кодом `422` с указанием фактического отклонения в пикселях.
* Если эталонный контур находится в статусе плейсхолдера 3D-художника, проверяется корректность нормализованных границ $0.0 \le x, y \le 1.0$.

### 4.3. Механика `none` (Интерактивный тап)
Не требует выполнения игровых условий — подтверждает взаимодействие со сценой и сразу выдает артефакт.

### 4.4. Эндпоинт симуляции: `POST /progress/verify/{location_id}`
Позволяет фронтенду протестировать расчет физики или геометрии без сохранения прогресса в БД.

---

## 5. Сессии, Прогресс и Паспорт

### Сессионная модель без авторизации
* Пользователю не требуется логин и пароль.
* При первом запуске мобильное/веб-приложение генерирует случайный UUID (например, `c9b1...`), сохраняет его локально на устройстве и передает во всех запросах к прогрессу и паспорту в заголовке:
  ```http
  X-Session-ID: 7b9a55e1-88c2-4a09-9f76-8051a8d05e21
  ```
* Бэкенд изолирует прогресс и паспорта разных сессий.

### Идемпотентность прогресса (`POST /progress/{location_id}`)
* Первое успешное прохождение точки сохраняет запись в БД и возвращает `is_new_unlock: true`.
* Повторный вызов эндпоинта на той же точке **не дублирует** артефакт в паспорте, не выдает ошибку, а возвращает `is_new_unlock: false` с датой исходного открытия.

### Паспорт (`GET /passport`)
* Возвращает текущее состояние сессии:
  * `total_slots`: общее количество слотов (для демо зафиксировано значение **10**).
  * `collected_count`: количество собранных артефактов.
  * `artifacts`: упорядоченный список собранных трофеев с метаданными и временными метками.

---

## 6. Интеграции с Yandex Cloud

### 6.1. Yandex Cloud Object Storage (S3)
* **Назначение**: хранение и раздача 3D-моделей (`.glb`), изображений маркеров и иконок трофеев.
* **Эндпоинт сервиса**: `https://storage.yandexcloud.net`.
* **Публичные ссылки**: при указании переменной `YANDEX_S3_PUBLIC_BASE_URL` относительные пути `models/...` автоматически преобразуются в прямые публичные ссылки для Three.js / WebGL.
* **API эндпоинты**:
  * `GET /storage/status` — проверка доступности бакета.
  * `POST /storage/presign-upload` — генерация подписанной ссылки для прямой загрузки клиентом в S3 (поддержка `onUploadProgress` / прогресс-бара без нагрузки на бэкенд).
  * `POST /storage/upload` — загрузка файла через сервер (3D-модель, маркер, иконка).
  * `GET /storage/presign/{key}` — генерация временной подписанной ссылки на скачивание.
  * `DELETE /storage/object/{key}` — удаление объекта из бакета.

### 6.2. Yandex LLM (YandexGPT / Alice AI) & Редакторский HITL
* **Назначение**:
  1. Виртуальный фольклорный гид по интерактивному маршруту (`POST /locations/{id}/chat`).
  2. **HITL-ассистент контент-редактора** (`POST /locations/editor/generate-content`): генерация вариантов описаний, реплик, подсказок и пасхалок по названию точки с режимом предварительного просмотра, ручной правки и утверждения (`POST /locations/{id}/editor/approve-content`).
* **Двойная совместимость**:
  * **OpenAI-совместимый HTTP API** (`https://llm.api.cloud.yandex.net/v1/chat/completions`) — для моделей нового поколения, таких как `aliceai-llm-flash`.
  * **Нативный Foundation Models API** (`https://llm.api.cloud.yandex.net/foundationModels/v1/completion`) — для стандартных моделей `yandexgpt/latest`.
  * **Демо-фоллбэк**: при отсутствии API-ключа сервис отвечает интеллектуальной фольклорной заглушкой.

---

## 7. Спецификация API (Endpoints)

Все эндпоинты доступны как напрямую от корня (`/locations`), так и с префиксом версии (`/api/v1/locations`).

### 7.1. Точки маршрута и Редактор (CRUD + HITL)

#### `GET /locations`
Возвращает полный упорядоченный список всех точек маршрута.

#### `POST /locations`
Создание новой точки маршрута (Редактор).
* **Тело запроса (`LocationCreateRequest`)**: `id`, `order`, `priority`, `title`, `mechanic`, `mechanic_params`, `marker`, `model_url`, `models`, `coordinates`, `animations`, `texts`, `artifact`, `next_location_*`.
* **Ответ `201 Created`**: созданный объект точки.
* **Ответ `409 Conflict`**: если точка с таким `id` уже существует.

#### `GET /locations/{id}`
Возвращает полную конфигурацию одной точки по ее ID.
* **Ответ `200 OK`**: JSON объект точки.
* **Ответ `404 Not Found`**: если точка не найдена.

#### `PUT /locations/{id}`
Обновление существующей точки маршрута (Редактор).
* **Тело запроса (`LocationUpdateRequest`)**: любые обновляемые поля точки.
* **Ответ `200 OK`**: обновленный объект точки.

#### `DELETE /locations/{id}`
Удаление точки маршрута и связанных записей прогресса.
* **Ответ `200 OK`**: `{"status": "deleted", "id": "..."}`.

#### `POST /locations/editor/generate-content`
**HITL Генерация контента**: принимает название точки и тему, возвращает несколько готовых вариантов описаний (`layer1`, `layer2`, `action_hint`, `dialogue`, `easter_egg`, `artifact_suggestion`).
* **Тело запроса**:
```json
{
  "title": "Озеро Кабан и водяная Су анасы",
  "context_or_theme": "золотой гребень, духи воды",
  "variant_count": 2
}
```
* **Ответ `200 OK`**:
```json
{
  "title": "Озеро Кабан и водяная Су анасы",
  "options": [
    {
      "variant_id": "variant_1_classic",
      "layer1": "Озеро Кабан — легендарная водная система в центре Казани...",
      "layer2": "По преданиям, на дне озера сокрыты ханские сокровища...",
      "action_hint": "Проведите пальцем по контуру золотого гребня...",
      "dialogue": [
        { "speaker": "Су анасы", "text": "Кто потревожил покой вод?", "trigger": "enter" }
      ],
      "easter_egg": "Легенда о золотом гребне...",
      "artifact_suggestion": { "id": "comb", "name": "Золотой гребень", "icon": "icons/comb.png" }
    }
  ],
  "model": "gpt://.../aliceai-llm-flash/latest",
  "is_mock": false
}
```

#### `POST /locations/{id}/editor/approve-content`
**HITL Аппрув-режим**: утверждение выбранного/отредактированного человеком варианта и сохранение в базу данных точки.
* **Тело запроса (`ApproveContentRequest`)**: `variant_id`, опциональные отредактированные поля `layer1`, `layer2`, `action_hint`, `dialogue`, `easter_egg`, `artifact_name`.
* **Ответ `200 OK`**: обновлённый объект локации.

#### `POST /storage/presign-upload`
Генерация пред-подписанной ссылки для **прямой загрузки файлов клиентом в S3 (Direct Upload)** с поддержкой прогресс-бара.
* **Тело запроса**:
```json
{
  "filename": "model_su_anasy.glb",
  "content_type": "model/gltf-binary",
  "key_prefix": "models"
}
```
* **Ответ `200 OK`**:
```json
{
  "key": "models/model_su_anasy.glb",
  "upload_url": "https://storage.yandexcloud.net/neuroart-kzn-assets/models/model_su_anasy.glb?X-Amz-Signature=...",
  "public_url": "https://storage.yandexcloud.net/neuroart-kzn-assets/models/model_su_anasy.glb",
  "method": "PUT",
  "content_type": "model/gltf-binary",
  "expires_in_seconds": 1800
}
```
*(Клиент отправляет файл методом `PUT` на `upload_url` и отслеживает событие `onUploadProgress` для отображения прогресс-бара).*

---


---

### 7.2. Прогресс и механики

#### `POST /progress/{location_id}`
Отмечает точку пройденной, валидирует телеметрию механики и добавляет артефакт в паспорт сессии.
* **Заголовок**: `X-Session-ID: <UUID>` (обязательный).
* **Тело запроса** (опционально, для валидации механики):
```json
{
  "taps_count": 35,
  "duration_seconds": 5.0
}
```
или для `trace`:
```json
{
  "user_path": [
    { "x": 0.1, "y": 0.2 },
    { "x": 0.3, "y": 0.22 },
    { "x": 0.8, "y": 0.25 }
  ],
  "screen_width": 1080.0
}
```
* **Ответ `200 OK`**:
```json
{
  "session_id": "7b9a55e1-88c2-4a09-9f76-8051a8d05e21",
  "location_id": "loc_2_sabantuy",
  "is_new_unlock": true,
  "artifact": {
    "id": "polotentse",
    "name": "Полотенце",
    "icon": "icons/polotentse.png"
  },
  "unlocked_at": "2026-09-10T20:15:00Z",
  "message": "Location completed successfully! Artifact unlocked.",
  "validation": {
    "success": true,
    "score": 123.3,
    "max_score_reached": 140.0,
    "message": "Victory! Climber grabbed the prize (effective score: 123.3/100)",
    "details": { "taps_count": 35, "duration_seconds": 5.0 }
  }
}
```
* **Ответ `422 Unprocessable Content`**: если условие механики не выполнено (не долез до верха столба или палец ушел за пределы допустимого отклонения).
* **Ответ `400 Bad Request`**: если не передан заголовок `X-Session-ID`.

#### `POST /progress/verify/{location_id}`
Тестирование и валидация телеметрии без изменения базы данных.

---

### 7.3. Паспорт

#### `GET /passport`
Возвращает текущее состояние паспорта сессии.
* **Заголовок**: `X-Session-ID: <UUID>` (обязательный).
* **Ответ `200 OK`**:
```json
{
  "session_id": "7b9a55e1-88c2-4a09-9f76-8051a8d05e21",
  "total_slots": 10,
  "collected_count": 2,
  "artifacts": [
    {
      "id": "klin",
      "name": "Клин",
      "icon": "icons/klin.png",
      "location_id": "loc_1_shurale",
      "unlocked_at": "2026-09-10T20:10:00Z"
    },
    {
      "id": "polotentse",
      "name": "Полотенце",
      "icon": "icons/polotentse.png",
      "location_id": "loc_2_sabantuy",
      "unlocked_at": "2026-09-10T20:15:00Z"
    }
  ]
}
```

---

### 7.4. AI-гид (YandexGPT)

#### `POST /locations/{id}/chat`
Отправляет вопрос виртуальному фольклорному гиду с учетом культурно-исторического контекста точки.
* **Тело запроса**:
```json
{
  "prompt": "Расскажи подробнее про шутку Шурале про имя Вгодуминувшем?",
  "history": []
}
```
* **Ответ `200 OK`**:
```json
{
  "location_id": "loc_1_shurale",
  "location_title": "Дровосек-батыр и Шурале",
  "answer": "В поэме Габдуллы Тукая дровосек хитро назвался именем 'Вгодуминувшем' (Былтыр)...",
  "model": "gpt://.../aliceai-llm-flash/latest",
  "is_mock": false
}
```

---

### 7.5. Хранилище (S3)

* `GET /storage/status` — проверка подключения к Yandex Object Storage.
* `POST /storage/upload` — загрузка файла в бакет (`multipart/form-data`, поля `file`, `key_prefix`).
* `GET /storage/presign/{key}` — получение временной подписанной ссылки на скачивание.
* `DELETE /storage/object/{key}` — удаление объекта.

---

### 7.6. Парсер точек (OSM) и рекомендатель квестов для редактора

Сервис парсит достопримечательности (POI) Казани из OpenStreetMap (Overpass API), выполняет автоматическую разметку категориями и семантическими тегами, предоставляет интерфейс модерации (HITL) для подтверждения тегов администратором и рекомендует релевантные точки редактору квестов.

#### Таксономия категорий и тегов:
* **Категории (`category`)**:
  * `monument` — памятники, монументы, мемориалы, скульптуры.
  * `museum_culture` — музеи, галереи, театры, культурные центры.
  * `historic_quarter` — исторические слободы, Кремль, древние усадьбы.
  * `nature_view` — парки, набережные, смотровые площадки, озера.
  * `folklore_legends` — фольклорные и сказочные персонажи (Зилант, Шурале, Кот Казанский).
  * `architecture_heritage` — архитектурные доминанты, исторические башни, храмы.
* **Семантические теги (`tags`)**:
  * `tatar_culture` — связь с татарской культурой и историей.
  * `unesco` — объекты всемирного наследия ЮНЕСКО.
  * `ar_friendly` — пешеходные зоны и площади, удобные для AR.
  * `waterfront` — расположение у воды (оз. Кабан, р. Казанка, р. Волга).
  * `photo_spot` — видовые точки и панорамы.
  * `family_friendly` — объекты для семейного и детского досуга.

#### Основные эндпоинты:

##### 1. `GET /poi/recommendations`
Умные рекомендации точек для редактора квестов с расчетом расстояния по формуле гаверсинусов, пересечения тегов и кураторских бейджей.
* **Параметры**:
  * `near_lat`, `near_lon`: координаты центра карты или предыдущей точки маршрута
  * `radius_meters`: радиус поиска в метрах (по умолчанию 2500 м)
  * `category`: фильтр по категории (`monument`, `museum_culture`, `historic_quarter`, `nature_view`, `folklore_legends`, `architecture_heritage`)
  * `tags`: список тегов через запятую (например, `tatar_culture,ar_friendly`)
  * `search`: текстовый поиск по названию или описанию
  * `status`: статус модерации (`approved` по умолчанию, `pending`, `all`)
  * `exclude_ids`: список ID уже добавленных в квест точек для исключения
  * `limit`: ограничение количества (по умолчанию 10)
* **Ответ `200 OK`**:
```json
[
  {
    "poi": {
      "id": "poi_node_node_10000002",
      "osm_id": "node/10000002",
      "osm_type": "node",
      "name": "Башня Сююмбике",
      "name_en": "Suyumbike Tower",
      "name_tt": "Сөембикә манарасы",
      "latitude": 55.7997,
      "longitude": 49.1055,
      "category": "architecture_heritage",
      "tags": ["unesco", "verified_quest_anchor", "photo_spot", "tatar_culture"],
      "description": "Проездная дозорная башня в Казанском кремле. Падающая башня, символ Казани.",
      "status": "approved",
      "confidence_score": 0.85
    },
    "distance_meters": 146.0,
    "match_score": 0.67,
    "reasons": [
      "В шаговой доступности (146 м)",
      "Проверено модератором"
    ]
  }
]
```

##### 2. `POST /poi/admin/{poi_id}/review`
Интерфейс модерации (HITL) для подтверждения или корректировки предложенных тегов администратором.
* **Тело запроса**:
```json
{
  "status": "approved",
  "category": "architecture_heritage",
  "tags": ["unesco", "verified_quest_anchor", "photo_spot", "tatar_culture"],
  "admin_notes": "Подтверждено главным куратором квестов"
}
```
* **Ответ `200 OK`**: обновленный объект POI со статусом `approved`.

##### 3. `POST /locations/from-poi`
Мгновенная конвертация рекомендованной точки интереса в активную точку интерактивного AR-маршрута (`Location`).
* **Тело запроса**:
```json
{
  "poi_id": "poi_node_node_10000002",
  "order": 4,
  "priority": "P1",
  "mechanic": "trace",
  "custom_title": "AR Квест: Башня Сююмбике"
}
```
* **Ответ `201 Created`**: полностью сформированный объект `LocationResponse` с авто-заполнением слоев текстов (`layer1`, `layer2`), параметров механики, маркера, 3D-модели и трофея для паспорта.

##### 4. Управление синхронизацией:
* `GET /poi/admin/pending` — список объектов, ожидающих модерации (поддерживает фильтрацию и пагинацию `limit`, `offset`).
* `POST /poi/admin/batch-approve` — пакетное подтверждение списка точек (`{"poi_ids": ["..."], "status": "approved"}`).
* `POST /poi/sync/run` — запуск синхронизации с Overpass API (`{"area_name": "Kazan", "force_remote": false, "dry_run": false}`).
* `GET /poi/sync/status` — статус базы POI, счетчики категорий и лог последних синхронизаций.

#### Запуск сервиса как автономного микросервиса:
Сервис спроектирован по модульной архитектуре и может запускаться как независимый микросервис на отдельном порту:
```powershell
uv run python -m app.services.poi.standalone --port 8001
```

---

## 8. Конфигурация переменных окружения (`.env`)

Все параметры конфигурируются в файле `.env` в корне проекта (шаблон в `.env.example`):

```dotenv
# Сервер
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENVIRONMENT=production

# База данных SQLite
DATABASE_URL=sqlite+aiosqlite:///./data/neuroart.db

# Настройки паспорта
PASSPORT_TOTAL_SLOTS=10

# Yandex Cloud Object Storage (S3)
YANDEX_S3_ENDPOINT_URL=https://storage.yandexcloud.net
YANDEX_S3_BUCKET_NAME=neuroart-kzn-assets
YANDEX_S3_ACCESS_KEY_ID=YCAJE...
YANDEX_S3_SECRET_ACCESS_KEY=YCP...
YANDEX_S3_REGION_NAME=ru-central1
YANDEX_S3_PUBLIC_BASE_URL=https://storage.yandexcloud.net/neuroart-kzn-assets

# Yandex LLM (YandexGPT / Alice)
YANDEX_GPT_API_KEY=AQVN...
YANDEX_GPT_FOLDER_ID=b1g...
YANDEX_GPT_MODEL_URI=gpt://b1g.../aliceai-llm-flash/latest
YANDEX_GPT_TEMPERATURE=0.6
YANDEX_GPT_MAX_TOKENS=1000
```

---

## 9. Запуск и разработка

### Установка зависимостей с помощью `uv`
```powershell
uv sync
```

### Запуск локального сервера разработки
```powershell
uv run uvicorn app.main:app --reload --port 8000
```
- **Панель администрирования и редактор квестов (Jinja2 SSR)**:
  [http://localhost:8000/admin](http://localhost:8000/admin)
  - `/admin` — Обзор метрик маршрута и статус сервисов
  - `/admin/quests` — Таблица и управление точками маршрута
  - `/admin/quests/{id}/edit` — Редактор точки квеста (параметры, лор, 3D, HITL YandexGPT ассистент)
  - `/admin/quests/new` — Создание новой точки маршрута
  - `/admin/pois` — Модерация культурных POI и конвертация в квест
  - `/admin/sync` — Синхронизация с OpenStreetMap Overpass
- **Интерактивная документация Swagger UI**:
  [http://localhost:8000/docs](http://localhost:8000/docs)

### Запуск через Docker Compose
```powershell
docker compose up --build -d
```

### Проверка боевых интеграций Yandex Cloud
```powershell
uv run python scripts/verify_yandex_integrations.py
```

### Проверка боевой разметки POI из OpenStreetMap
```powershell
uv run python scripts/verify_poi_tagging_live.py
```

### Демонстрация сценария редактора квестов
```powershell
uv run python scripts/demo_editor_flow.py
```

### Запуск полного набора автотестов
```powershell
uv run pytest -v
```
*(Комплекс из **49 автотестов** проверяет POI парсер и тегирование, HITL-модерацию, рекомендации для редактора, CRUD локаций, каскадное удаление прогресса, схемы паспорта, изоляцию сессий, физику механик, загрузку в S3 и генерацию контента Yandex LLM).*

