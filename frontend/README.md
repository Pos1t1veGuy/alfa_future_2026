# Frontend

React + TypeScript + Vite интерфейс Альфа-Бизнес. Основные экраны используют Django REST API через `src/api/client.ts`; MSW не запускается.

## Разработка

```bash
npm ci
npm run dev
```

Vite проксирует `/api/*` на `http://localhost:8000`. Запустите backend и PostgreSQL через Docker Compose.

## Сборка

```bash
npm run build
```

Для контейнерного запуска используйте корневую инструкцию README. Настройка `VITE_API_URL` задаёт базовый URL API (по умолчанию `/api/v1`).
