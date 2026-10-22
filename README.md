# Альфа-Бизнес — кредитный кабинет

Демонстрационный MVP: предприниматель регистрируется, выбирает кредитный продукт, отправляет заявку и документы; сотрудник банка видит очередь и меняет статус заявки. Данные и действия в основных сценариях сохраняются в PostgreSQL через Django REST API. Фронтенд больше не запускает MSW и не использует demo-массивы для экранов кабинета.

## Запуск

1. Создайте `.env` в корне проекта. Минимальные локальные значения:

```dotenv
POSTGRES_DB=alfa_hack
POSTGRES_USER=alfa_user
POSTGRES_PASSWORD=change_me
DB_HOST=db
DB_PORT=5432
DB_NAME=alfa_hack
DB_USER=alfa_user
DB_PASSWORD=change_me
DJANGO_SECRET_KEY=replace_with_a_long_random_secret
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1
VITE_API_URL=/api/v1
VITE_USE_MOCKS=false
```

2. Запустите сервисы:

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend
```

Frontend: http://localhost  
Django API: http://localhost:8000/api/v1/

3. Регистрация предпринимателя доступна на стартовом экране. Для локального демонстрационного кабинета сотрудника compose выполняет `seed_demo`:

- Email: `manager@alfa.local`
- Пароль: `DemoManager2026!`

Эти демонстрационные учётные данные нельзя использовать в публичной/боевой среде. Перед любым общим развёртыванием измените или удалите команду `seed_demo` и задайте собственный секрет Django.

## Реализованные API

- `POST /api/v1/auth/register/`, `POST /api/v1/auth/login/`, `POST /api/v1/auth/refresh/`, `GET/PATCH /api/v1/me/`
- `GET /api/v1/products/`
- `GET/POST /api/v1/applications/`, `GET/PATCH /api/v1/applications/{id}/`, `GET /api/v1/bank/applications/`
- `POST /api/v1/documents/`, `POST /api/v1/documents/{id}/ocr/`
- `POST /api/v1/safe-limit/calculate/`
- `GET /api/v1/notifications/`, `POST /api/v1/notifications/read-all/`, `POST /api/v1/notifications/{id}/read/`

JWT access/refresh хранится в localStorage для демонстрационного SPA. OCR и расчёт безопасного лимита используют упрощённые демонстрационные правила, не банковское решение. Для промышленного использования потребуются полноценные тесты, объектное хранилище документов, аудит, rate limiting, управление ролями и миграции схемы.

## Важно

- `.env` не добавляйте в Git.
- Локальный Vite использует proxy на `localhost:8000`; Docker/Nginx проксирует `/api/` к backend.
- `VITE_USE_MOCKS` оставлен для совместимости с прежним `.env`, но `main.tsx` не запускает MSW.
