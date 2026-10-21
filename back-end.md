ЧАСТЬ 2. API_CONTRACTS.md
Документ для бэкенд-разработчика. Формат: метод, путь, роль, тело, ответ, ошибки. Все даты — ISO 8601 UTC (2026-10-20T12:34:56Z). Все суммы — в копейках (integer) или в рублях (число) — зафиксировать одно и указать в README. Ниже — рубли как number.

2.1. Общие соглашения
Базовый URL: /api/v1

Аутентификация: Bearer JWT (access + refresh), Authorization: Bearer <access>.

Формат ошибки:

json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Некорректные данные",
    "details": [
      { "field": "requested_amount", "message": "Сумма превышает лимит продукта" }
    ]
  }
}
Коды ошибок: VALIDATION_ERROR, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, CONFLICT, INVALID_STATE_TRANSITION, INTERNAL_ERROR.

Заголовки:

X-Idempotency-Key — для POST /submit и POST /decision.

X-Request-Id — для трассировки.

Пагинация: ?page=1&pageSize=20, ответ:

json
{ "items": [...], "total": 42, "page": 1, "pageSize": 20 }
2.2. Модуль Auth
POST /auth/login
Request:

json
{ "email": "client@example.com", "password": "secret" }
Response 200:

json
{
  "accessToken": "jwt...",
  "refreshToken": "jwt...",
  "expiresIn": 900,
  "user": {
    "id": "uuid",
    "email": "client@example.com",
    "fullName": "Иван Петров",
    "role": "client",
    "companyId": "uuid",
    "companyRole": "owner"
  }
}
Ошибки: 401 UNAUTHORIZED.

POST /auth/refresh
Request: { "refreshToken": "jwt..." }
Response 200: { "accessToken": "...", "expiresIn": 900 }

POST /auth/logout
Request: { "refreshToken": "jwt..." }
Response 204.

GET /me
Response 200:

json
{
  "id": "uuid",
  "email": "client@example.com",
  "fullName": "Иван Петров",
  "role": "client",
  "companyId": "uuid",
  "companyRole": "owner"
}
2.3. Модуль Companies
GET /companies/{id}
Роль: client (своя) / bank_manager / admin.

Response 200:

json
{
  "id": "uuid",
  "type": "LLC",
  "inn": "7701234567",
  "ogrn": "1157746000000",
  "name": "ООО «Ромашка»",
  "shortName": "Ромашка",
  "okved": "62.01",
  "okvedDescription": "Разработка ПО",
  "registrationDate": "2021-03-15",
  "taxRegime": "USN",
  "address": "г. Москва, ул. ...",
  "revenue": {
    "avgMonthlyRevenue": 1200000,
    "avgMonthlyExpenses": 900000,
    "periodMonths": 12
  },
  "employeesCount": 15,
  "hasPreviousBusinesses": false
}
PATCH /companies/{id}
Роль: client с companyRole=owner|finance.
Поля: revenue, employeesCount, address.
Response 200 — обновлённая компания.

2.4. Модуль Products
GET /products
Роль: любой auth.

Query: ?minAmount=&maxAmount=&term=&type=.
Response 200:

json
{
  "items": [
    {
      "id": "uuid",
      "code": "MICROLOAN_FAST",
      "name": "Микрозайм «Быстрый»",
      "type": "microloan",
      "minAmount": 100000,
      "maxAmount": 5000000,
      "minTermMonths": 3,
      "maxTermMonths": 24,
      "interestRate": 18.5,
      "description": "...",
      "requirements": ["Срок деятельности ≥ 6 мес.", "Выручка ≥ 300 000 ₽/мес"],
      "isRecommended": true
    }
  ]
}
GET /products/{id}
Response 200 — один продукт.

2.5. Модуль Applications (клиент)
POST /applications
Роль: client.

Request:

json
{
  "productId": "uuid",
  "requestedAmount": 1000000,
  "requestedTermMonths": 12,
  "purpose": "Пополнение оборотных средств"
}
Response 201:

json
{ "id": "uuid", "status": "DRAFT", "createdAt": "2026-10-20T12:00:00Z" }
GET /applications
Роль: client (только свои).

Query: ?status=&page=&pageSize=&sort=.
Response 200 — пагинированный список:

json
{
  "items": [
    {
      "id": "uuid",
      "number": "APP-2026-000123",
      "productId": "uuid",
      "productName": "Микрозайм «Быстрый»",
      "requestedAmount": 1000000,
      "status": "SCORING",
      "createdAt": "...",
      "updatedAt": "..."
    }
  ],
  "total": 5, "page": 1, "pageSize": 20
}
GET /applications/{id}
Роль: client (своя) / bank_manager.

Response 200 — полная карточка:

json
{
  "id": "uuid",
  "number": "APP-2026-000123",
  "status": "MANUAL_REVIEW",
  "currentStage": "manual_review",
  "product": { "id": "uuid", "name": "..." },
  "company": { "id": "uuid", "name": "..." },
  "applicant": { "id": "uuid", "fullName": "...", "role": "director" },
  "requestedAmount": 1000000,
  "requestedTermMonths": 12,
  "purpose": "...",
  "createdAt": "...",
  "updatedAt": "...",
  "assignedManagerId": "uuid|null",
  "decision": null,
  "safeLimit": {
    "min": 400000, "max": 600000, "calculatedAt": "..."
  }
}
PATCH /applications/{id}
Роль: client, только при status=DRAFT.
Request: частичное обновление полей мастера.
Response 200 — обновлённая заявка.

POST /applications/{id}/submit
Роль: client. Заголовок X-Idempotency-Key.
Request: пустое тело или финальная сводка.
Response 202:

json
{ "status": "SUBMITTED", "submittedAt": "..." }
Ошибки: 409 INVALID_STATE_TRANSITION если не DRAFT; 422 VALIDATION_ERROR если не заполнены обязательные поля.

POST /applications/{id}/cancel
Роль: client.
Response 200: { "status": "CANCELLED" }.
Ошибки: 409 если уже финальный статус.

POST /applications/{id}/supplement
Роль: client, только при status=NEEDS_INFO.

Request:

json
{
  "fields": { "requestedAmount": 700000 },
  "documentIds": ["uuid"]
}
Response 200: { "status": "DATA_ENRICHMENT" }.

GET /applications/{id}/history
Роль: client / bank_manager.

Response 200:

json
{
  "items": [
    {
      "id": "uuid",
      "status": "SUBMITTED",
      "changedAt": "...",
      "changedBy": { "id": "uuid", "name": "Клиент" },
      "comment": null
    },
    {
      "id": "uuid",
      "status": "NEEDS_INFO",
      "changedAt": "...",
      "changedBy": { "id": "uuid", "name": "Менеджер" },
      "comment": "Нужна выписка за 6 месяцев"
    }
  ]
}
2.6. Модуль Documents и OCR
POST /documents
Multipart: file, applicationId, type (financial_statement|tax_declaration|charter|passport|other).
Response 201:

json
{ "id": "uuid", "filename": "statement.pdf", "size": 123456, "status": "UPLOADED" }
Ошибки: 413 при превышении размера, 415 при неверном типе.

GET /applications/{id}/documents
Response 200 — список документов.

POST /documents/{id}/ocr
Роль: client / bank_manager.

Response 200:

json
{
  "documentId": "uuid",
  "status": "PARSED",
  "confidence": 0.92,
  "extractedFields": {
    "inn": "7701234567",
    "revenue": 14400000,
    "periodFrom": "2025-01-01",
    "periodTo": "2025-12-31",
    "companyName": "ООО «Ромашка»"
  }
}
Ошибки: 422 если не удалось распознать.

DELETE /documents/{id}
Response 204. Только при status=DRAFT или NEEDS_INFO.

2.7. Модуль Safe Limit Calculator
POST /safe-limit/calculate
Роль: client / bank_manager.

Request:

json
{
  "avgMonthlyRevenue": 1200000,
  "avgMonthlyExpenses": 900000,
  "existingMonthlyDebt": 50000,
  "businessAgeMonths": 30,
  "industry": "it",
  "hasPreviousBusinesses": false,
  "requestedAmount": 1000000,
  "requestedTermMonths": 12
}
Response 200:

json
{
  "safeMin": 400000,
  "safeMax": 600000,
  "pdnBefore": 0.04,
  "pdnAfter": 0.14,
  "riskLevel": "low",
  "recommendation": "Запрошенная сумма превышает безопасный диапазон",
  "factors": [
    { "code": "revenue_multiplier", "impact": "negative", "description": "Сумма > 0.8× среднемесячной выручки" },
    { "code": "pdn", "impact": "positive", "description": "ПДН после оформления в норме" }
  ]
}
2.8. Модуль External Checks (моки)
POST /applications/{id}/checks/run
Роль: bank_manager / система (вызывается автоматически после submit).
Request: { "providers": ["egrul", "fns", "bki"] }.
Response 202: { "status": "RUNNING" }.

GET /applications/{id}/checks
Response 200:

json
{
  "items": [
    {
      "provider": "egrul",
      "status": "SUCCESS",
      "checkedAt": "...",
      "data": { "companyStatus": "ACTIVE", "registrationDate": "2021-03-15" }
    },
    {
      "provider": "fns",
      "status": "SUCCESS",
      "data": { "taxRegime": "USN", "debtExists": false }
    },
    {
      "provider": "bki",
      "status": "SUCCESS",
      "data": { "creditHistoryScore": 720, "activeLoans": 2, "overdueCount": 0 }
    }
  ]
}
2.9. Модуль Scoring и Decision
GET /applications/{id}/scoring
Роль: bank_manager.

Response 200:

json
{
  "score": 745,
  "riskLevel": "low",
  "model": "rule-based-v1",
  "calculatedAt": "...",
  "factors": [
    { "code": "credit_history", "impact": "positive", "weight": 0.25, "description": "..." },
    { "code": "debt_load", "impact": "negative", "weight": 0.15, "description": "..." }
  ]
}
POST /applications/{id}/decision
Роль: bank_manager. Заголовок X-Idempotency-Key.

Request:

json
{
  "decision": "APPROVED_WITH_CHANGES",
  "approvedAmount": 600000,
  "approvedTermMonths": 12,
  "approvedRate": 19.5,
  "reason": "Сумма снижена согласно ПДН",
  "reasonCode": "DEBT_LOAD_ADJUSTMENT"
}
Возможные decision: APPROVED, APPROVED_WITH_CHANGES, NEEDS_INFO, REJECTED.

Для NEEDS_INFO дополнительно:

json
{ "requestedFields": ["financial_statement_6m"], "comment": "..." }
Для REJECTED:

json
{ "reasonCode": "INSUFFICIENT_HISTORY", "comment": "..." }
Response 200:

json
{ "status": "APPROVED_WITH_CHANGES", "decidedAt": "...", "decidedBy": { "id": "uuid", "name": "..." } }
Ошибки: 409 INVALID_STATE_TRANSITION если заявка не в MANUAL_REVIEW.

POST /applications/{id}/assign
Роль: bank_manager.
Request: { "managerId": "uuid" } или пусто для «на себя».
Response 200.

GET /bank/applications
Роль: bank_manager.

Query: ?status=&productId=&onlyMine=&search=&page=&pageSize=&sort=.
Response 200 — пагинированный список (как GET /applications, но с полями клиента и менеджера).

GET /rejection-reasons
Роль: bank_manager.

Response 200:

json
{ "items": [{ "code": "INSUFFICIENT_HISTORY", "label": "Недостаточная кредитная история" }] }
2.10. Модуль Documents Signing (мок)
POST /applications/{id}/documents/sign
Роль: client.

Request: { "documentIds": ["uuid"] }.
Response 200: { "status": "SIGNED", "signedAt": "..." }.

POST /applications/{id}/disburse
Роль: bank_manager (мок выдачи).

Response 200: { "status": "DISBURSED", "disbursedAt": "..." }.

2.11. Модуль Notifications
GET /notifications
Роль: auth.

Query: ?unreadOnly=true&page=.
Response 200:

json
{
  "items": [
    {
      "id": "uuid",
      "type": "STATUS_CHANGED",
      "title": "Статус заявки изменён",
      "body": "Заявка APP-2026-000123 перешла в «Одобрено»",
      "applicationId": "uuid",
      "isRead": false,
      "createdAt": "..."
    }
  ],
  "total": 3
}
POST /notifications/{id}/read → 204
POST /notifications/read-all → 204
2.12. WebSocket-контракты
ws/applications/{id}/status/
Авторизация: ?token=<access> в query (WS не поддерживает заголовки).

Событие:

json
{
  "type": "application.status_changed",
  "applicationId": "uuid",
  "status": "APPROVED",
  "stage": "decision",
  "changedAt": "...",
  "payload": {
    "approvedAmount": 600000,
    "comment": "Сумма снижена"
  }
}
ws/notifications/
Событие:

json
{
  "type": "notification.created",
  "notification": { ... как в GET /notifications ... }
}
Общие требования:

Публикация событий — только после коммита в БД (transaction.on_commit).

Реконнект-политика на клиенте — backoff.

Авторизация — JWT в query.

Heartbeat-ping каждые 30 сек (опционально).

2.13. State Machine заявки
text
DRAFT
  → SUBMITTED
  → VALIDATION
  → DATA_ENRICHMENT
  → SCORING
  → MANUAL_REVIEW
  → APPROVED | APPROVED_WITH_CHANGES | NEEDS_INFO | REJECTED
NEEDS_INFO
  → DATA_ENRICHMENT (после supplement)
APPROVED | APPROVED_WITH_CHANGES
  → DOCUMENTS_SIGNING
  → DISBURSED
Любой нефинальный
  → CANCELLED
Правила:

Переходы разрешены только по таблице.

Каждый переход создаёт запись в ApplicationStatusHistory.

Запрещённые переходы → 409 INVALID_STATE_TRANSITION.

2.14. Матрица прав
Эндпоинт	client	bank_manager	admin
POST /applications	✅	❌	✅
PATCH /applications/{id} (DRAFT)	✅ (своя)	❌	✅
POST /applications/{id}/submit	✅ (своя)	❌	✅
POST /applications/{id}/supplement	✅ (своя)	❌	✅
GET /applications/{id}	✅ (своя)	✅	✅
GET /bank/applications	❌	✅	✅
POST /applications/{id}/decision	❌	✅	✅
POST /applications/{id}/assign	❌	✅	✅
GET /applications/{id}/scoring	❌	✅	✅
GET /applications/{id}/checks	❌ (только статус)	✅	✅
POST /safe-limit/calculate	✅	✅	✅
POST /documents/{id}/ocr	✅ (свой)	✅	✅
POST /applications/{id}/documents/sign	✅ (своя)	❌	✅
POST /applications/{id}/disburse	❌	✅	✅
2.15. Что отдать бэкенду одним сообщением
Формат ошибок и коды.

Все эндпоинты по модулям с примерами request/response.

State machine и правила переходов.

Матрицу прав.

WebSocket-события и требования к публикации после коммита.

Требование: все внешние проверки (ЕГРЮЛ, ФНС, БКИ) и OCR — моки с фиксированными сценариями, описанными в README.

Требование: X-Idempotency-Key на submit и decision.

Требование: ApplicationStatusHistory пишется на каждый переход.

Синтетика: 3 компании, 5 продуктов, 6 заявок в разных статусах, 2 менеджера, 1 админ.

OpenAPI/Swagger — генерировать через drf-spectacular, отдать фронту для генерации типов.