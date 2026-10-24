# Alfa Future - фактический API backend

Статус: актуально по исходникам `backend/hack2026_site/core/` и локальной проверке API 24.10.2026.

Этот документ описывает **то, что сейчас реально запускается**, а не целевой контракт из `back-end.md` / `BACKEND_API_CONTRACT.md`.

## Быстрые контакты

| Назначение | Адрес |
| --- | --- |
| REST API из Docker | `http://localhost:8000/api/v1/` |
| Frontend через Nginx | `http://localhost/api/v1/` |
| Frontend в Vite dev | `http://localhost:5173/api/v1/` (Vite proxy -> `localhost:8000`) |
| Админка Django | `http://localhost:8000/admin/` |

Все пути ниже идут после `/api/v1/`. Формат дат - ISO 8601 UTC. Суммы - целые рубли.

## Авторизация

Для защищённых запросов нужен заголовок:

```http
Authorization: Bearer <accessToken>
```

Роли: `client`, `bank_manager`, `admin`.

### `POST /auth/register/`

Создаёт только клиента и сразу возвращает JWT.

```json
{
  "fullName": "Иван Иванов",
  "email": "ivan@example.com",
  "password": "SecurePassword123!",
  "company": "ООО Альфа",
  "inn": "7701234567",
  "phone": "+79991234567"
}
```

Обязательные поля: `fullName`, `email`, `password`, `company`.

Ответ `201 Created`:

```json
{
  "accessToken": "<jwt-access-token>",
  "refreshToken": "<jwt-refresh-token>",
  "user": {
    "id": "1",
    "email": "ivan@example.com",
    "fullName": "Иван Иванов",
    "role": "client",
    "company": "ООО Альфа",
    "inn": "7701234567",
    "phone": "+79991234567"
  }
}
```

Ошибки: `400` с объектом полевых ошибок, например:

```json
{ "email": ["Аккаунт с таким email уже существует."] }
```

### `POST /auth/login/`

Несмотря на то, что идентификатор - email, backend ожидает его в поле `username`.

```json
{
  "username": "manager@alfa.local",
  "password": "DemoManager2026!"
}
```

Ответ `200 OK` имеет те же поля `accessToken`, `refreshToken`, `user`, что и регистрация.

Ошибка неверных реквизитов: `401 Unauthorized`:

```json
{
  "detail": "No active account found with the given credentials"
}
```

### `POST /auth/refresh/`

```json
{ "refresh": "<jwt-refresh-token>" }
```

Ответ `200 OK`:

```json
{ "access": "<new-jwt-access-token>" }
```

Важно: здесь используются поля `refresh` и `access`, а не `refreshToken` / `accessToken`.

### `POST /auth/logout/`

Требует Bearer token. Тело необязательно; frontend передаёт `refreshToken`.

```json
{ "refreshToken": "<jwt-refresh-token>" }
```

Ответ `204 No Content`. Refresh-токен не заносится в blacklist: logout выполняется удалением токенов на frontend.

### `GET /me/` и `PATCH /me/`

`GET` возвращает объект `user` из login/register.

`PATCH` поддерживает:

```json
{
  "fullName": "Иван Петров",
  "company": "ООО Альфа",
  "inn": "7701234567",
  "phone": "+79990000000"
}
```

Все поля необязательны. Ответ `200 OK` - обновлённый профиль.

## Кредитные продукты

### `GET /products/`

Требует авторизацию. Единственный поддерживаемый фильтр - `?minAmount=1000000`.

Ответ `200 OK`:

```json
{
  "items": [
    {
      "id": "turnover",
      "name": "На пополнение оборотных средств",
      "description": "Закупайте товар, оплачивайте аренду и закрывайте кассовые разрывы.",
      "rate": "от 18,5%",
      "maxAmount": 10000000,
      "term": "до 36 месяцев",
      "icon": "↻",
      "minTermMonths": 3,
      "maxTermMonths": 36
    }
  ],
  "total": 3
}
```

Демо-продукты `turnover`, `equipment`, `universal` создаются backend автоматически при первом обращении.

## Заявки

Статусы, которые реально допускает модель:

| API-значение | Значение в интерфейсе |
| --- | --- |
| `draft` | Черновик |
| `submitted` | Заявка принята |
| `review` | Рассматривается |
| `additional_info` | Нужны уточнения |
| `approved` | Одобрено |
| `declined` | Не одобрено |

### `GET /applications/`

Клиент получает только свои заявки; `bank_manager` и `admin` получают все. У банковских ролей работают `?status=` и `?search=`.

Ответ `200 OK`:

```json
{
  "items": [
    {
      "id": "CR-ABC123",
      "productId": "turnover",
      "productName": "На пополнение оборотных средств",
      "amount": 2500000,
      "termMonths": 24,
      "purpose": "Закупка оборудования",
      "company": "ООО Альфа",
      "inn": "7701234567",
      "contact_name": "Иван Иванов",
      "phone": "+79991234567",
      "status": "submitted",
      "createdAt": "2026-10-24T02:00:00Z",
      "updatedAt": "2026-10-24T02:00:00Z",
      "clientName": "Иван Иванов",
      "historyItems": [],
      "managerName": "",
      "decision_comment": ""
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 1
}
```

Пагинация пока номинальная: массив `items` не разбивается на страницы.

### `GET /bank/applications/`

Маршрут использует тот же view, что и `GET /applications/`. У банковских ролей ответ и фильтры такие же. В текущем backend отсутствует отдельная проверка роли именно на URL `/bank/applications/` - клиент, если вызовет этот URL, увидит свои заявки, а не получит `403`.

### `POST /applications/`

Создаёт и сразу отправляет заявку (`status = submitted`), черновики отдельно не создаются.

```json
{
  "productId": "turnover",
  "amount": 2500000,
  "termMonths": 24,
  "purpose": "Пополнение оборотных средств",
  "company": "ООО Альфа",
  "inn": "7701234567",
  "phone": "+79991234567",
  "contactName": "Иван Иванов"
}
```

Ответ `201 Created` - полный объект заявки, как элемент `items` выше. Backend добавляет историю `submitted` и уведомление клиенту.

Ошибки:

| Код | Когда | Реальный ответ |
| --- | --- | --- |
| `400` | Некорректная сумма | `{ "message": "Сумма должна быть от 1 до 10000000 ₽." }` |
| `400` | Некорректный срок | `{ "message": "Срок не подходит для выбранного продукта." }` |
| `400` | Сумма/срок не число | `{ "message": "Проверьте сумму и срок." }` |
| `404` | Не существует `productId` | `{ "detail": "No Product matches the given query." }` |

Технически этот endpoint сейчас разрешён любой аутентифицированной роли, хотя продуктово он должен быть доступен только клиенту.

### `GET /applications/{id}/`

Полная карточка. Доступна владельцу, `bank_manager` и `admin`.

Ответ `200 OK` - объект заявки, включающий `historyItems`, `managerName` и `decision_comment`.

Ошибки:

| Код | Реальный ответ |
| --- | --- |
| `403` | `{ "message": "Нет доступа" }` |
| `404` | `{ "detail": "No LoanApplication matches the given query." }` |

### `PATCH /applications/{id}/`

Меняет решение. Разрешён только `bank_manager` / `admin`.

```json
{
  "status": "additional_info",
  "comment": "Пожалуйста, приложите выписку по расчётному счёту."
}
```

Допустимые статусы: `review`, `additional_info`, `approved`, `declined`.

Ответ `200 OK` - обновлённый объект заявки. Если менеджер не был назначен, backend назначает текущего сотрудника. Создаются история и уведомление клиенту.

Ошибки:

| Код | Реальный ответ |
| --- | --- |
| `400` | `{ "message": "Недопустимый статус." }` |
| `403` для клиента | `{ "message": "Изменять заявку можно только через поддержку." }` |
| `403` нет доступа к заявке | `{ "message": "Нет доступа" }` |
| `404` | `{ "detail": "No LoanApplication matches the given query." }` |

### `POST /applications/{id}/submit-additional-info/`

Клиент повторно отправляет заявку после запроса уточнений. Тело не нужно.

Условия: клиент - владелец, статус `additional_info`, загружен хотя бы один документ.

Ответ `200 OK` - объект заявки со статусом `review`.

Ошибки:

| Код | Реальный ответ |
| --- | --- |
| `400` неверный статус | `{ "message": "Отправить документы можно, когда банк запросил уточнения." }` |
| `400` нет файлов | `{ "message": "Сначала прикрепите хотя бы один документ." }` |
| `403` | `{ "message": "Только владелец заявки может отправить уточнения." }` |
| `404` | `{ "detail": "No LoanApplication matches the given query." }` |

## Документы и OCR

### `GET /documents/?applicationId={id}`

Владелец заявки, менеджер или администратор могут получить список файлов.

Ответ `200 OK`:

```json
{
  "items": [
    {
      "id": "12",
      "filename": "statement.pdf",
      "size": 204800,
      "status": "UPLOADED",
      "createdAt": "2026-10-24T02:00:00Z"
    }
  ]
}
```

Ошибки: `400` без `applicationId`, `403` доступа нет, `404` заявки нет.

### `GET /documents/{id}/download/`

Защищённый просмотр или скачивание прикреплённого PDF/JPG/PNG. Файл отдаётся только владельцу заявки, менеджеру или администратору; публичной ссылки на файл нет. Ответ `200 OK` содержит бинарное содержимое с исходным именем файла.

Ошибки:

| Код | Реальный ответ |
| --- | --- |
| `403` | `{ "message": "Нет доступа к документу." }` |
| `404` нет записи | `{ "detail": "No UploadedDocument matches the given query." }` |
| `404` нет файла в хранилище | `{ "message": "Файл не найден в хранилище." }` |

### `POST /documents/`

`multipart/form-data`:

| Поле | Тип | Обязательное |
| --- | --- | --- |
| `file` | File | Да |
| `applicationId` | String | Да |
| `type` | String | Нет, пока игнорируется backend |

Поддерживаются `pdf`, `jpg`, `jpeg`, `png`; ограничение - 10 МБ.

Ответ `201 Created`:

```json
{ "id": "12", "filename": "statement.pdf", "size": 204800, "status": "UPLOADED" }
```

Ошибки:

| Код | Реальный ответ |
| --- | --- |
| `400` без файла | `{ "message": "Выберите файл для загрузки." }` |
| `403` | `{ "message": "Нет доступа к заявке." }` |
| `404` | `{ "detail": "No LoanApplication matches the given query." }` |
| `413` | `{ "message": "Максимальный размер файла — 10 МБ." }` |
| `415` | `{ "message": "Поддерживаются PDF, JPG и PNG." }` |

### `POST /documents/{id}/ocr/`

Запускает демо-OCR для владельца, менеджера или администратора.

Ответ `200 OK`:

```json
{
  "documentId": "12",
  "status": "PARSED",
  "confidence": 0.94,
  "extractedFields": {
    "inn": "7701234567",
    "revenue": 1500000,
    "companyName": "ООО Альфа"
  }
}
```

Ошибки: `403` - `{ "message": "Нет доступа к документу." }`; `404` - `{ "detail": "No UploadedDocument matches the given query." }`.

## Калькулятор безопасного лимита

### `POST /safe-limit/calculate/`

```json
{
  "avgMonthlyRevenue": 1500000,
  "avgMonthlyExpenses": 900000,
  "existingMonthlyDebt": 40000,
  "requestedAmount": 1000000
}
```

Ответ `200 OK`:

```json
{
  "safeMin": 2547999,
  "safeMax": 3919999,
  "pdnBefore": 0.027,
  "pdnAfter": 0.082,
  "riskLevel": "low",
  "recommendation": "Ориентировочный расчёт. Финальное решение принимает банк.",
  "factors": []
}
```

Ошибка `400`: `{ "message": "Укажите числовые значения." }`.

В текущем коде не используются поля `businessAgeMonths`, `industry`, `requestedTermMonths` и т. п., если frontend передаст их дополнительно.

## Уведомления

### `GET /notifications/`

Поддерживает `?unreadOnly=true`.

Ответ `200 OK`:

```json
{
  "items": [
    {
      "id": 1,
      "title": "Заявка отправлена",
      "body": "Заявка CR-ABC123 принята и передана в банк.",
      "isRead": false,
      "createdAt": "2026-10-24T02:00:00Z",
      "applicationId": "CR-ABC123"
    }
  ],
  "total": 1
}
```

### `POST /notifications/read-all/`

Помечает все непрочитанные уведомления текущего пользователя прочитанными. Ответ `204 No Content`.

### `POST /notifications/{id}/read/`

Помечает одно уведомление прочитанным. Ответ `204 No Content`.

Если уведомление отсутствует или принадлежит другому пользователю: `404` с `detail` от DRF.

## Общие ошибки и границы реализации

Проверенный фактический формат не единый. Он зависит от endpoint'а:

| Код | Формат / пример |
| --- | --- |
| `400` | Обычно `{ "message": "..." }`; у serializer'ов регистрации - полевой объект `{ "email": ["..."] }` |
| `401` | `{ "detail": "Authentication credentials were not provided." }` |
| `403` | Обычно `{ "message": "..." }` |
| `404` | `{ "detail": "No <Model> matches the given query." }` |
| `405` | Стандартный DRF: `{ "detail": "Method \"DELETE\" not allowed." }` |
| `413` | `{ "message": "Максимальный размер файла — 10 МБ." }` |
| `415` | `{ "message": "Поддерживаются PDF, JPG и PNG." }` |
| `409`, `422` | В коде сейчас не формируются |

Локально проверены: `200 /products/`, `200 /bank/applications/`, `200 /safe-limit/calculate/`, `404` для несуществующего продукта/заявки и `401` без Bearer token.

## Сверка с frontend и присланным контрактом

### Совпадает сейчас

Runtime-frontend уже обращается к реальному backend через `src/api/client.ts` и `/api/v1`:

- login/register/refresh/me;
- продукты, список и карточка заявок;
- создание заявки и банковский `PATCH` решения;
- документы, OCR и повторная отправка уточнений;
- калькулятор безопасного лимита;
- уведомления и профиль.

`main.tsx` не запускает MSW. Старые файлы `src/api/mocks/` и `src/mock/` лежат в репозитории, но не импортируются в рабочий маршрут приложения и не участвуют в API-вызовах.

### Не совпадает с целевым/старым контрактом

Ниже - функции, описанные в `back-end.md` и ранних ТЗ, но пока отсутствующие в реально запущенном Django:

- черновики и `PATCH` заявки клиентом;
- `POST /applications/{id}/submit`, `/cancel`, `/supplement`;
- отдельные endpoint'ы истории, удаления/скачивания документа и документов заявки;
- решение с новой суммой/ставкой/сроком, причины отказа и валидация переходов;
- настоящая пагинация, сортировка, расширенные фильтры;
- WebSocket/Django Channels, polling fallback как серверная функция;
- `APPROVED_WITH_CHANGES`, `DISBURSED`, `NEEDS_INFO`, `DATA_ENRICHMENT`, `MANUAL_REVIEW`;
- единый error envelope, `X-Idempotency-Key`, `409` / `422`;
- CORS middleware для прямых междоменных вызовов и выдача URL для скачивания документов.

Итог: с **присланным описанием реально реализованных маршрутов** frontend и backend сходятся по используемым операциям. С более широким целевым контрактом из старой документации они пока не сходятся - этот документ фиксирует точную границу.
