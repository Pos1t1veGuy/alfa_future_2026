# API-контракт backend для «Умного кредитного кабинета»

Версия: `v1`  
Базовый URL: `/api/v1`  
Формат: `application/json`, даты - ISO 8601 UTC.

Этот документ описывает минимальный контракт для Django + Django REST Framework + PostgreSQL. Внешние проверки ЕГРЮЛ/ФНС/БКИ в MVP реализуются локальными моками.

## 1. Авторизация и роли

Роли:

- `client` - представитель компании, создаёт и отслеживает заявки;
- `bank_manager` - рассматривает заявки и принимает решения;
- `admin` - полный доступ.

### POST `/auth/login/`

Тело:

```json
{
  "email": "i.sokolova@example.test",
  "password": "demo-password"
}
```

Ответ `200`:

```json
{
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token",
  "user": {
    "id": "uuid",
    "name": "Ирина Соколова",
    "email": "i.sokolova@example.test",
    "role": "client",
    "company": { "id": "uuid", "name": "ООО «Вектор»", "inn": "7704123456" }
  }
}
```

### POST `/auth/refresh/`

Тело: `{ "refresh": "jwt-refresh-token" }`.  
Ответ: `{ "access": "новый-access-token" }`.

### POST `/auth/logout/`

Тело: `{ "refresh": "jwt-refresh-token" }`. Добавляет refresh-токен в blacklist.

### GET `/auth/me/`

Возвращает текущего пользователя и компанию. Все защищённые запросы используют заголовок `Authorization: Bearer <access>`.

## 2. Справочник продуктов

### GET `/products/`

Доступен авторизованным пользователям.

Параметры фильтрации: `amount`, `term_months`.

Ответ `200`:

```json
[
  {
    "id": "turnover",
    "name": "На пополнение оборотных средств",
    "description": "Закупки, аренда и кассовые разрывы",
    "min_amount": 100000,
    "max_amount": 10000000,
    "min_term_months": 3,
    "max_term_months": 36,
    "rate_from": "18.50",
    "is_active": true
  }
]
```

## 3. Заявки клиента

### Статусы

| Значение API | Текст для клиента | Доступные действия клиента |
| --- | --- | --- |
| `DRAFT` | Черновик | Редактировать, удалить, отправить |
| `SUBMITTED` | Заявка принята | Смотреть статус, отменить |
| `REVIEW` | Рассматривается | Смотреть статус |
| `MANUAL_REVIEW` | Нужна ручная проверка | Смотреть статус |
| `ADDITIONAL_INFO` | Нужны уточнения | Дополнить информацию |
| `APPROVED` | Одобрено | Подписать документы |
| `APPROVED_CHANGED` | Одобрено с изменениями | Принять условия, подписать документы |
| `DECLINED` | Не одобрено | Смотреть причину |
| `CANCELLED` | Отменена | Нет |

Нельзя переводить статус непосредственно на фронтенде: все переходы валидируются в сервисном слое backend.

### GET `/applications/`

Для `client` возвращает только его заявки. Для банка используется отдельный endpoint очереди.

Параметры: `status`, `page`, `page_size`, `ordering`.

Ответ `200`:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "CR-482901",
      "product": { "id": "turnover", "name": "На пополнение оборотных средств" },
      "amount": 2500000,
      "term_months": 24,
      "purpose": "Закупка сезонного товара",
      "status": "REVIEW",
      "created_at": "2026-10-18T08:30:00Z",
      "updated_at": "2026-10-18T08:32:00Z",
      "unread_events_count": 1
    }
  ]
}
```

### POST `/applications/`

Создаёт черновик или сразу отправляет заявку. Обязателен заголовок `Idempotency-Key: <uuid>`.

```json
{
  "product_id": "turnover",
  "amount": 2500000,
  "term_months": 24,
  "purpose": "Закупка сезонного товара",
  "company": {
    "name": "ООО «Вектор»",
    "inn": "7704123456",
    "okved": "47.19",
    "phone": "+79991234567"
  },
  "applicant": {
    "full_name": "Ирина Соколова",
    "position": "Генеральный директор",
    "phone": "+79991234567",
    "email": "i.sokolova@example.test"
  },
  "submit": false
}
```

`submit: false` создаёт `DRAFT`; `submit: true` запускает конвейер и создаёт `SUBMITTED`.

Ответ `201`: полная карточка заявки.

### GET `/applications/{application_id}/`

Возвращает полную клиентскую карточку: заявка, результат, история статусов, документы, запросы информации.

```json
{
  "id": "CR-482901",
  "status": "REVIEW",
  "status_message": "Проверяем данные компании и готовим решение",
  "product": { "id": "turnover", "name": "На пополнение оборотных средств" },
  "amount": 2500000,
  "term_months": 24,
  "purpose": "Закупка сезонного товара",
  "history": [
    {
      "id": "uuid",
      "status": "REVIEW",
      "created_at": "2026-10-18T08:32:00Z",
      "actor": { "name": "Кредитный конвейер", "type": "system" },
      "comment": "Проводим автоматические проверки"
    }
  ],
  "documents": [],
  "additional_info_requests": [],
  "decision": null
}
```

### PATCH `/applications/{application_id}/`

Редактирование разрешено только в `DRAFT` и только владельцу. Поля аналогичны `POST`.

### POST `/applications/{application_id}/submit/`

Отправляет черновик. Обязателен `Idempotency-Key`. Переводит `DRAFT` в `SUBMITTED`.

### POST `/applications/{application_id}/cancel/`

Доступно для `DRAFT` и `SUBMITTED`. Тело: `{ "reason": "Передумал оформлять" }`.

### POST `/applications/{application_id}/documents/`

`multipart/form-data`: `file`, `document_type`. Лимит и разрешённые типы проверяются backend (`pdf`, `jpg`, `jpeg`, `png`, до 10 МБ).

### DELETE `/applications/{application_id}/documents/{document_id}/`

Удаление доступно владельцу, пока документ не подписан/не зафиксирован решением.

### POST `/applications/{application_id}/additional-info/`

Клиент отвечает на запрос банка. Обязателен `Idempotency-Key`.

```json
{
  "request_id": "uuid",
  "fields": { "annual_revenue": 18000000 },
  "comment": "Добавили выписку и оборот за год"
}
```

Переводит заявку из `ADDITIONAL_INFO` в `REVIEW`.

### POST `/applications/{application_id}/sign/`

Моделирует подписание. Допустим только для `APPROVED`/`APPROVED_CHANGED`.

## 4. Банковский кабинет

Все endpoint’ы раздела требуют роль `bank_manager` или `admin`.

### GET `/bank/applications/`

Параметры:

- `status`, `product_id`, `min_amount`, `max_amount`;
- `created_from`, `created_to`, `assigned_to_me`;
- `search` - номер, клиент, компания;
- `ordering` - `created_at`, `-created_at`, `amount`, `-amount`;
- `page`, `page_size`.

Ответ - пагинированный список с номером, клиентом, компанией, продуктом, суммой, статусом, датой и менеджером.

### GET `/bank/applications/{application_id}/`

Расширенная карточка: данные клиента/компании, документы, история, внешние проверки, скоринг и внутренние комментарии.

```json
{
  "id": "CR-482901",
  "company": { "name": "ООО «Вектор»", "inn": "7704123456", "okved": "47.19" },
  "checks": [
    { "source": "EGRUL", "status": "PASSED", "summary": "Компания активна" },
    { "source": "BKI", "status": "PASSED", "summary": "Критических просрочек нет" }
  ],
  "scoring": {
    "score": 74,
    "risk_level": "MEDIUM",
    "factors": [
      { "title": "Стабильность оборотов", "impact": "positive" },
      { "title": "Долговая нагрузка", "impact": "negative" }
    ]
  },
  "allowed_actions": ["ASSIGN_TO_ME", "APPROVE", "REQUEST_INFO", "DECLINE"]
}
```

`allowed_actions` - источник истины для доступности кнопок на frontend.

### POST `/bank/applications/{application_id}/assign/`

Тело: `{ "manager_id": "uuid" }`. Менеджер может назначить себя; admin - любого доступного менеджера.

### POST `/bank/applications/{application_id}/decision/`

Единая точка принятия решения. Обязателен `Idempotency-Key`.

```json
{
  "decision": "APPROVE",
  "approved_amount": 2500000,
  "approved_term_months": 24,
  "rate": "18.50",
  "client_comment": "Одобрено на запрошенных условиях",
  "internal_comment": "Проверки завершены"
}
```

Допустимые `decision`:

- `APPROVE` -> `APPROVED`;
- `APPROVE_CHANGED` -> `APPROVED_CHANGED`, обязательны новые сумма/срок/ставка и причина;
- `REQUEST_INFO` -> `ADDITIONAL_INFO`, обязательны `requested_fields` и `client_comment`;
- `DECLINE` -> `DECLINED`, обязательны `decline_reason_code` и текст для клиента.

### POST `/bank/applications/{application_id}/comments/`

```json
{ "body": "Ожидаем подтверждение оборотов", "visibility": "internal" }
```

`visibility` пока разрешать только `internal`; клиентские комментарии можно добавить позднее.

## 5. Уведомления

### GET `/notifications/`

Параметры: `is_read`, `page`, `page_size`.

### POST `/notifications/{notification_id}/read/`

Помечает одно уведомление прочитанным.

### POST `/notifications/read-all/`

Помечает все уведомления текущего пользователя прочитанными.

## 6. WebSocket и polling fallback

Подключать после базового REST-контура через Django Channels.

- `ws/applications/{application_id}/status/?token=<access_jwt>` - события карточки доступной пользователю заявки;
- `ws/notifications/?token=<access_jwt>` - новые уведомления и изменение счётчика.

Событие:

```json
{
  "type": "application.status_changed",
  "application_id": "CR-482901",
  "status": "ADDITIONAL_INFO",
  "status_message": "Нужна выписка по расчётному счёту",
  "history_item": { "id": "uuid", "created_at": "2026-10-18T12:00:00Z" }
}
```

Если WS недоступен, frontend вызывает `GET /applications/{id}/` каждые 15 секунд, пока пользователь находится на карточке. Для очереди банка - `GET /bank/applications/?updated_after=<timestamp>` каждые 20 секунд.

## 7. Ошибки и правила

Единый формат ошибок:

```json
{
  "code": "validation_error",
  "message": "Проверьте заполненные поля",
  "fields": { "amount": ["Сумма превышает лимит продукта"] }
}
```

- `400` - ошибка данных/недопустимый переход статуса;
- `401` - access-токен истёк; frontend пытается refresh один раз;
- `403` - нет роли или доступа к конкретной заявке;
- `404` - объект не найден;
- `409` - конфликт: заявка уже обработана либо повторный idempotency key с другим телом;
- `413` - превышен размер документа;
- `429` - лимит запросов;
- `500` - не раскрывать технические детали клиенту.

## 8. Минимальные Django-модели

- `User` (роль, контакты);
- `Company` (ИНН, ОГРН, ОКВЭД, реквизиты);
- `CreditProduct`;
- `CreditApplication` (клиент, компания, продукт, сумма, срок, цель, статус, назначенный менеджер, timestamps);
- `ApplicationStatusHistory` (заявка, статус, actor, comment, timestamp);
- `ApplicationDocument`;
- `AdditionalInfoRequest`;
- `ExternalCheck`;
- `ScoringResult` и `ScoringFactor`;
- `Decision`;
- `InternalComment`;
- `Notification`;
- `IdempotencyRecord`.

Ключевая бизнес-логика переходов, скоринга, прав и решений должна находиться в Django service layer, а не во view/serializer и не на frontend.
