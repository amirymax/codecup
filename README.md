# CodeCup.tech

Платформа онлайн-контестов для разработчиков.

- **Backend** — Django 5.2 + Django REST Framework + PostgreSQL (корень репозитория)
- **Frontend** — Next.js 15 + TypeScript + Tailwind + shadcn/ui (`/frontend`)
- **Auth** — только через Telegram-бота
- **Язык интерфейса** — русский

План разработки: [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

---

## Локальный запуск

Нужны Python 3.12+, Docker и Node 20+.

```bash
cp .env.example .env          # затем впишите DJANGO_SECRET_KEY
make install                  # виртуальное окружение и зависимости
make up                       # Postgres в Docker
make migrate
make run                      # http://127.0.0.1:8000
```

Проверка: `curl http://127.0.0.1:8000/api/health/` → `{"status":"ok","database":"ok"}`

| Адрес | Назначение |
|---|---|
| `/api/health/` | состояние сервиса и базы |
| `/api/docs/` | Swagger UI |
| `/api/schema/` | схема OpenAPI |
| `/admin/` | админка Django |

Команды: `make help`. Тесты — `make test`, стиль — `make lint` и `make format`,
пересоздать базу с нуля — `make reset-db`.
