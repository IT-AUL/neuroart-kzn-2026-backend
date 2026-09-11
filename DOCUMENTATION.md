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
│   │       ├── locations.py         # GET /locations, GET /locations/{id}
│   │       ├── progress.py          # POST /progress/{location_id}, POST /progress/verify/{id}
│   │       ├── passport.py          # GET /passport
│   │       ├── ai.py                # POST /locations/{id}/chat (YandexGPT гид)
│   │       └── storage.py           # Статус S3, загрузка ассетов, presigned URL
│   ├── core/
│   │   ├── config.py                # Pydantic Settings конфигурация
│   │   ├── database.py              # Асинхронный движок SQLAlchemy и фабрика сессий
│   │   └── exceptions.py            # Кастомные HTTP-исключения
│   ├── db/
│   │   ├── base.py                  # Базовый класс моделей SQLAlchemy
│   │   ├── models/
│   │   │   ├── location.py          # ORM-модель точки маршрута с JSON-полями
│   │   │   └── progress.py          # ORM-модель прогресса сессии и трофеев
│   │   └── seeds/
│   │       ├── initial_data.py      # Фиксированные данные трех точек маршрута
│   │       └── seeder.py            # Идемпотентный сидер БД при старте сервиса
│   ├── schemas/
│   │   ├── location.py              # Схемы Pydantic точек, координат, маркеров, параметров механик
│   │   ├── passport.py              # Схемы паспорта и собранных артефактов
│   │   ├── progress.py              # Схемы отправки телеметрии прохождения и ответа
│   │   ├── storage.py               # Схемы ответов S3
│   │   └── ai.py                    # Схемы запросов и ответов диалога с LLM
│   ├── services/
│   │   ├── location_service.py      # Бизнес-логика точек и резолва URL моделей
│   │   ├── passport_service.py      # Учет прогресса, слоты паспорта, идемпотентность
│   │   ├── s3_service.py            # Клиент Yandex Object Storage (загрузка, presigned URL)
│   │   ├── yandex_llm_service.py    # Клиент YandexGPT (OpenAI-совместимый и нативный протоколы)
│   │   └── mechanics/               # Движок валидации и физики игровых механик
│   │       ├── base.py              # Базовый интерфейс валидатора механик
│   │       ├── trace.py             # Геометрическая валидация обводки контура (trace)
│   │       ├── tap_climb.py         # Физическая симуляция лазания на столб (tap_climb)
│   │       └── none_mechanic.py     # Логика точек без мини-игры (none)
│   └── main.py                      # Точка входа, lifespan (авто-создание таблиц и сидинг), CORS
├── scripts/
│   └── verify_yandex_integrations.py # Скрипт проверки боевого подключения к S3 и LLM
├── tests/                           # Комплекс автоматических тестов (22 теста)
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
  * `easter_egg`: `ЗАПОЛНИТЬ!!!!`
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
  * `layer2`: `ЗАПОЛНИТЬ!!!!`
  * `action_hint`: «Здесь можно просто отдохнуть с дороги. Тапните по чак-чаку, чтобы положить угощение в альбом.»
  * `dialogue`: реплика хозяйки стола.
  * `easter_egg`: `ЗАПОЛНИТЬ!!!!`
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
Интерактивная документация Swagger UI доступна по адресу:
[http://localhost:8000/docs](http://localhost:8000/docs)

### Запуск через Docker Compose
```powershell
docker compose up --build -d
```

### Проверка боевых интеграций Yandex Cloud
```powershell
uv run python scripts/verify_yandex_integrations.py
```

### Запуск полного набора автотестов
```powershell
uv run pytest -v
```
*(Все 22 теста проверяют схемы, эндпоинты, идемпотентность, изоляцию сессий, физику механик, загрузку S3 и ответы LLM).*
