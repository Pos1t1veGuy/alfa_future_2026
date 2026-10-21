# Умный кредитный кабинет предпринимателя

MVP для хакатона Альфа-Банка: личный кабинет малого и микробизнеса, который проводит клиента от выбора финансирования к результату по заявке.

## Стек

- Backend: Python 3.11, Django, Django REST Framework, PostgreSQL; Django Channels подключается после базового REST-конвейера.
- Frontend: React, TypeScript, Vite.
- Infrastructure: Docker / Docker Compose, Nginx для production frontend.

## Frontend

Исходный код и контракт с backend находятся в [frontend/README.md](frontend/README.md).

## MVP-сценарий

1. Предприниматель выбирает кредитный продукт.
2. Указывает сумму, срок и цель.
3. Создаётся заявка со статусом `submitted`.
4. Клиент видит этапы обработки и новости по заявке.
5. Backend-правила переводят её в `review`, `additional_info`, `approved` или `declined`.

## Что нужно подготовить команде

- `docker-compose.yml` для frontend, Django и PostgreSQL;
- OpenAPI/Swagger из DRF;
- диаграмму состояний заявки и модель данных;
- синтетические компании, заявки, финансовые показатели и мок-проверки БКИ/ЕГРЮЛ;
- правила скоринга и принятия решения, явно обозначенные как упрощённые;
- тестовые сценарии, `THIRD_PARTY_NOTICES` и инструкции запуска.
