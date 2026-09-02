#!/usr/bin/env bash
# Первичная установка на чистом сервере. Выполняется один раз.
# Пакеты (nginx, certbot, node, postgres) и база должны быть уже готовы.
set -euo pipefail

REPO="${REPO:-git@github.com:amirymax/codecup.git}"
APP=/opt/codecup

echo "==> Код"
if [ ! -d "$APP/.git" ]; then
    git clone --quiet "$REPO" "$APP"
fi
cd "$APP"

echo "==> Виртуальное окружение"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements/prod.txt

echo "==> Каталоги"
mkdir -p media staticfiles

if [ ! -f .env ]; then
    echo "СТОП: создайте /opt/codecup/.env (см. .env.prod.example)"
    exit 1
fi
if [ ! -f .env.frontend ]; then
    echo "СТОП: создайте /opt/codecup/.env.frontend (см. .env.frontend.example)"
    exit 1
fi

echo "==> Сервисы"
cp deploy/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --quiet codecup-api codecup-web codecup-bot

echo "==> nginx"
cp deploy/nginx/codecup.conf /etc/nginx/sites-available/codecup.conf
ln -sf /etc/nginx/sites-available/codecup.conf /etc/nginx/sites-enabled/codecup.conf
rm -f /etc/nginx/sites-enabled/default

echo "Готово. Дальше: сертификаты (certbot), затем deploy/deploy.sh"
