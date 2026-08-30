# Развёртывание CodeCup.tech

Backend, фронтенд и nginx работают в контейнерах. **Postgres в контейнеры не
входит** — на сервере он устанавливается отдельно, со своим обновлением и
бэкапом. Так база переживает пересборку приложения, а её данные не зависят
от жизни Docker-томов.

```
            ┌────────── nginx (443) ──────────┐
            │                                  │
   codecup.tech                        api.codecup.tech
            │                                  │
       frontend:3000                      backend:8000
     (Next.js standalone)              (Django + gunicorn)
                                              │
                                      Postgres на хосте
```

Домены соседние не случайно: кука сессии выставлена с `SameSite=Lax` и
`AUTH_COOKIE_DOMAIN=.codecup.tech`, поэтому она уходит и на сайт, и на API.
Разнести их на разные домены нельзя — вход перестанет работать.

## Первая установка

### 1. Postgres на сервере

```bash
sudo apt update && sudo apt install -y postgresql
sudo -u postgres psql <<'SQL'
CREATE USER codecup WITH PASSWORD 'ПРИДУМАЙТЕ_ПАРОЛЬ';
CREATE DATABASE codecup OWNER codecup;
SQL
```

Чтобы контейнер видел базу, Postgres должен слушать адрес docker-моста:

```bash
# /etc/postgresql/*/main/postgresql.conf
listen_addresses = 'localhost,172.17.0.1'

# /etc/postgresql/*/main/pg_hba.conf
host  codecup  codecup  172.16.0.0/12  scram-sha-256
```

```bash
sudo systemctl restart postgresql
```

### 2. Код и настройки

```bash
sudo mkdir -p /opt/codecup && sudo chown "$USER" /opt/codecup
git clone https://github.com/amirymax/codecup.git /opt/codecup
cd /opt/codecup
cp .env.prod.example .env.prod
```

Заполните `.env.prod`. Ключ Django генерируется так:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Тем же способом получите `TELEGRAM_WEBHOOK_SECRET`.

### 3. Сертификаты

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d codecup.tech -d www.codecup.tech -d api.codecup.tech
mkdir -p deploy/certs
sudo cp /etc/letsencrypt/live/codecup.tech/fullchain.pem deploy/certs/
sudo cp /etc/letsencrypt/live/codecup.tech/privkey.pem   deploy/certs/
```

Продление — в cron, с копированием файлов и перезапуском nginx:

```
0 4 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/codecup.tech/*.pem /opt/codecup/deploy/certs/ && docker compose -f /opt/codecup/docker-compose.prod.yml restart nginx
```

### 4. Запуск

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate
docker compose -f docker-compose.prod.yml run --rm backend python manage.py createsuperuser
docker compose -f docker-compose.prod.yml up -d
```

### 5. Вебхук Telegram

```bash
docker compose -f docker-compose.prod.yml exec backend \
    python manage.py set_webhook https://api.codecup.tech
```

Проверка: `curl https://api.codecup.tech/api/health/` → `{"status":"ok",...}`

### 6. Бэкапы

```bash
sudo crontab -e
# 0 3 * * * /opt/codecup/deploy/backup.sh >> /var/log/codecup-backup.log 2>&1
```

Скрипт хранит дампы 14 дней и завершается ошибкой, если дамп оказался
пустым, — молча положить в архив нечитаемый файл хуже, чем упасть.

## Обновление

```bash
cd /opt/codecup && ./deploy/deploy.sh
```

Скрипт забирает изменения, пересобирает образы, применяет миграции,
перезапускает сервисы и ждёт, пока backend ответит на `/api/health/`.
Если не дождался — показывает логи и завершается с ошибкой.

## Восстановление из бэкапа

```bash
docker compose -f docker-compose.prod.yml stop backend frontend
gunzip -c /var/backups/codecup/codecup_ГГГГ-ММ-ДД_ЧЧ-ММ.sql.gz | \
    sudo -u postgres psql codecup
docker compose -f docker-compose.prod.yml start backend frontend
```

## Если что-то не работает

| Симптом | Причина |
|---|---|
| Бесконечный редирект на https | nginx не передаёт `X-Forwarded-Proto` |
| Вход не сохраняется | `AUTH_COOKIE_DOMAIN` не совпадает с доменом, или сайт открыт по http |
| Бот молчит | вебхук не зарегистрирован либо `TELEGRAM_WEBHOOK_SECRET` разъехался с тем, что в `.env.prod` |
| `502` от nginx | backend не поднялся: `docker compose -f docker-compose.prod.yml logs backend` |
| Нет стилей в админке | образ собран без `collectstatic` — пересоберите backend |

Проверка настроек безопасности:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py check --deploy
```
