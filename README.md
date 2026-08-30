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

---

## Вход через Telegram

Аутентификация устроена так: сайт выдаёт одноразовый код, пользователь
подтверждает вход в боте, сайт обменивает код на сессию в httpOnly-куках.

```
Браузер                     Backend                      Telegram
  │ POST /api/auth/telegram/start/ │
  │◀── nonce + client_secret ──────│
  │ открывает t.me/<бот>?start=<nonce> ────────────────────▶│
  │                                │◀── вебхук /start <nonce>│
  │                                │─ «Подтвердить вход?» ──▶│
  │ опрос status/ раз в 2 сек      │                         │
  │                                │◀── нажата кнопка ───────│
  │◀── {"status":"confirmed"} ─────│
  │ POST exchange/ {nonce, client_secret}                    │
  │◀── Set-Cookie: cc_access, cc_refresh ──                  │
```

`nonce` проходит через Telegram открытым текстом, поэтому сам по себе он
сессию не даёт: обменять его можно только вместе с `client_secret`, который
остался в браузере. Код одноразовый и живёт 5 минут — по истечении срока
экран входа показывает «Ссылка устарела».

### Настройка бота локально

1. Получите токен у [@BotFather](https://t.me/BotFather) и впишите в `.env`
   `TELEGRAM_BOT_TOKEN` и `TELEGRAM_BOT_USERNAME`.
2. Придумайте `TELEGRAM_WEBHOOK_SECRET` — любая случайная строка.
3. Поднимите туннель, чтобы Telegram достучался до localhost:

   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

4. Зарегистрируйте вебхук на выданный адрес:

   ```bash
   .venv/bin/python manage.py set_webhook https://ваш-туннель.trycloudflare.com
   ```

Снять вебхук — `manage.py delete_webhook`. Тесты бота не ходят в сеть и
проходят без токена.

### Эндпоинты авторизации

| Метод | Адрес | Назначение |
|---|---|---|
| POST | `/api/auth/telegram/start/` | выдать код и ссылку на бота |
| GET | `/api/auth/telegram/status/?nonce=` | статус подтверждения (опрос) |
| POST | `/api/auth/telegram/exchange/` | обменять код на сессию |
| POST | `/api/auth/refresh/` | обновить сессию |
| POST | `/api/auth/logout/` | выйти |
| GET | `/api/auth/me/` | текущий пользователь |

---

## Контесты

`status` — это решение администратора (`draft` / `published` / `archived`), а
`state`, который видит пользователь, вычисляется на чтение из статуса и
дедлайна: `draft`, `live`, `ended`, `archived`. Поэтому контест не может
остаться «идущим» после дедлайна и для перевода в завершённые не нужен ни
cron, ни очередь.

Названия на русском транслитерируются в латинский слаг:
«Создайте инструмент на базе ИИ» → `sozdayte-instrument-na-baze-ii`.
При переименовании контеста слаг не меняется, чтобы не ломать ссылки.

| Метод | Адрес | Доступ | Назначение |
|---|---|---|---|
| GET | `/api/contests/` | все | список, фильтр `?state=live\|ended` |
| GET | `/api/contests/featured/` | все | контест для главной |
| GET | `/api/contests/<slug>/` | все | страница контеста |
| POST/DELETE | `/api/me/notify/` | участник | «Уведомить меня» |
| GET/POST | `/api/admin/contests/` | админ | список и создание |
| GET/PATCH/DELETE | `/api/admin/contests/<id>/` | админ | правка и удаление |
| POST | `/api/admin/contests/<id>/publish/` | админ | публикация |

`featured` всегда отвечает объектом `{"contest": ...}`, где `contest` равен
`null`, если активного контеста нет — это состояние «Сейчас нет активного
контеста» на главной.

Демо-данные из макетов: `.venv/bin/python manage.py seed_demo`.
