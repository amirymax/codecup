# Развёртывание CodeCup.tech

Всё работает прямо на сервере, без контейнеров: Postgres из пакетов Ubuntu,
Django под gunicorn, Next.js под node, всё это — systemd-сервисы за nginx.

```
        nginx (80/443)
        ├── codecup.tech      → 127.0.0.1:3000   codecup-web   (Next.js)
        └── api.codecup.tech  → 127.0.0.1:8000   codecup-api   (gunicorn)
                                                 codecup-bot   (Telegram)
                                                 Postgres 16   (localhost)
```

Домены соседние не случайно: кука сессии выставлена с `SameSite=Lax` и
`AUTH_COOKIE_DOMAIN=.codecup.tech`, поэтому уходит и на сайт, и на API.
Развести их на разные домены нельзя — вход перестанет работать.

## Первая установка

Предполагается Ubuntu 24.04 с установленными postgresql, nginx, certbot,
node 22 и python3-venv.

```bash
# 1. База
sudo -u postgres psql -c "CREATE USER codecup WITH PASSWORD 'пароль';"
sudo -u postgres createdb -O codecup codecup

# 2. Код и сервисы
export REPO=git@github.com:amirymax/codecup.git
curl -fsSL https://raw.githubusercontent.com/amirymax/codecup/main/deploy/bootstrap.sh | bash
# остановится и попросит создать /opt/codecup/.env

# 3. Настройки
cp /opt/codecup/.env.prod.example /opt/codecup/.env
nano /opt/codecup/.env          # заполнить, ключ: python3 -c "import secrets; print(secrets.token_urlsafe(64))"
bash /opt/codecup/deploy/bootstrap.sh

# 4. Сертификаты (DNS уже должен указывать на сервер)
# До выпуска на 80 порту стоит codecup-http.conf — он нужен только для
# проверки Let's Encrypt. После выпуска ставим полный конфиг с TLS.
certbot certonly --webroot -w /var/www/html \
    -d codecup.tech -d www.codecup.tech -d api.codecup.tech \
    --agree-tos -m ВАШ@EMAIL --non-interactive

cp /opt/codecup/deploy/nginx/codecup.conf /etc/nginx/sites-available/codecup.conf
nginx -t && systemctl reload nginx

# 5. Выкатка
/opt/codecup/deploy/deploy.sh

# 6. Администратор
cd /opt/codecup && .venv/bin/python manage.py make_admin --telegram-username AmiriCode
```

Проверка: `curl https://api.codecup.tech/api/health/` → `{"status":"ok",...}`

## Обновление

Пуш в `main` → CI → автоматическая выкатка (`.github/workflows/deploy.yml`).
Выкатывается только то, что прошло проверки: deploy запускается по успешному
завершению CI, а не по самому пушу.

Вручную — то же самое:

```bash
/opt/codecup/deploy/deploy.sh
```

Скрипт забирает код, ставит зависимости, применяет миграции, собирает статику
и фронтенд, перезапускает сервисы и ждёт ответа от `/api/health/`.

### Секреты в GitHub

Для автовыкатки в репозитории нужны три секрета:

| Секрет | Значение |
|---|---|
| `SERVER_HOST` | 178.105.106.8 |
| `SERVER_USER` | root |
| `SERVER_SSH_KEY` | приватный ключ, публичная часть которого лежит в `~/.ssh/authorized_keys` на сервере |

И **deploy key** самого репозитория (Settings → Deploy keys, read-only) —
публичная часть `/root/.ssh/codecup_deploy.pub` с сервера, чтобы `git pull`
работал.

## Сервисы

```bash
systemctl status codecup-api codecup-web codecup-bot
journalctl -u codecup-api -f
systemctl restart codecup-bot
```

## Бэкапы

```bash
crontab -e
# 0 3 * * * /opt/codecup/deploy/backup.sh >> /var/log/codecup-backup.log 2>&1
```

## Автопроверка заявок

```bash
crontab -e
# */10 * * * * cd /opt/codecup && .venv/bin/python manage.py screen_submissions >> /var/log/codecup-screening.log 2>&1
```

## Если что-то не работает

| Симптом | Причина |
|---|---|
| Бесконечный редирект на https | nginx не передаёт `X-Forwarded-Proto` |
| Вход не сохраняется | `AUTH_COOKIE_DOMAIN` не совпадает с доменом |
| Бот молчит | `systemctl status codecup-bot`, проверьте `TELEGRAM_BOT_TOKEN` |
| `502` от nginx | сервис не поднялся: `journalctl -u codecup-api -n 50` |
| Нет стилей | `collectstatic` не отработал — запустите `deploy.sh` заново |
| «Application error: a server-side exception» на всех страницах | сервер Next.js не достучался до API: проверьте `INTERNAL_API_URL` в `.env.frontend` и `journalctl -u codecup-web -n 30` |
| `fatal: detected dubious ownership` при выкатке | `/opt/codecup` принадлежит не root: `chown -R root:root /opt/codecup` |
