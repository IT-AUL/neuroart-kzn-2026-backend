# neuroart-kzn-2026-backend

Что нужно сделать:

Хранилище точек маршрута (locations). Модель данных: id, order, priority, mechanic (trace / tap_climb / none), mechanic_params, marker, model_url, coordinates, animations (id + имя), texts (layer1 + layer2), artifact. Полное наполнение по всем трем точкам уже готово.
Эндпоинты: GET /locations, GET /locations/{id}, POST /progress/{location_id}, GET /passport.
Сессия без авторизации, session_id с устройства в заголовке, бэк группирует прогресс по нему.
Паспорт: список собранных артефактов, общее число слотов (10 для демо), счетчик собранных.