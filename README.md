# NeuroArt KZN 2026 Backend

Бэкенд-сервис интерактивного туристического AR-маршрута по Казани на **FastAPI**, **SQLite**, **Yandex Object Storage (S3)** и **Yandex LLM (YandexGPT / Alice)**.

Полная и подробная документация доступна в файле [DOCUMENTATION.md](DOCUMENTATION.md).

---

## Быстрый старт

### 1. Установка зависимостей через `uv`
```powershell
uv sync
```

### 2. Настройка переменных окружения
Скопируйте шаблон и укажите ваши ключи в `.env`:
```powershell
Copy-Item .env.example .env
```

### 3. Запуск локального сервера разработки
```powershell
uv run uvicorn app.main:app --reload --port 8000
```
Swagger UI документация: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Запуск тестов
```powershell
uv run pytest -v
```

### 5. Запуск через Docker Compose
```powershell
docker compose up --build -d
```

---

## Ключевые возможности

1. **Хранилище точек маршрута (`GET /locations`, `GET /locations/{id}`)**:
   - Точка 1: *Дровосек-батыр и Шурале* (механика `trace`, обводка трещины бревна с `tolerance: 20px`).
   - Точка 2: *Сабантуй, лазание на столб* (механика `tap_climb`, физика подъема и затухания, порог 100).
   - Точка 3: *Чаепитие и чак-чак* (механика `none`, трофей по первому тапу).
2. **Сессионный паспорт (`GET /passport`, `POST /progress/{location_id}`)**:
   - Учет по `X-Session-ID` (без авторизации).
   - Идемпотентность — повторные вызовы не дублируют артефакты.
   - 10 слотов паспорта в демо-версии.
3. **Серверная валидация механик (`app/services/mechanics/`)**:
   - Моделирование физики затухания и частоты тапов (`tap_climb`).
   - Геометрическая проверка точности обводки контура (`trace`).
   - Эндпоинт симуляции: `POST /progress/verify/{location_id}`.
4. **Интеграция с Yandex Cloud**:
   - **Object Storage (S3)**: хранение и прямая раздача 3D моделей `.glb`, маркеров и иконок.
   - **Yandex LLM (YandexGPT / Alice)**: контекстный фольклорный гид (`POST /locations/{id}/chat`).