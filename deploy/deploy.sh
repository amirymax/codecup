#!/usr/bin/env bash
# Выкатка на сервере. Запускается вручную или из GitHub Actions по push в main.
set -euo pipefail

cd /opt/codecup

echo "==> Забираю код"
git fetch --quiet origin main
git reset --hard --quiet origin/main

echo "==> Зависимости backend"
.venv/bin/pip install --quiet -r requirements/prod.txt

echo "==> Миграции"
.venv/bin/python manage.py migrate --noinput

echo "==> Статика"
.venv/bin/python manage.py collectstatic --noinput --clear > /dev/null

echo "==> Сборка фронтенда"
cd frontend
npm ci --silent
npm run build > /dev/null
# standalone-сборка не копирует статику и public — переносим руками.
cp -r .next/static .next/standalone/.next/static
[ -d public ] && cp -r public .next/standalone/public
cd ..

echo "==> Перезапуск"
systemctl restart codecup-api codecup-web codecup-bot

echo "==> Проверка"
for _ in $(seq 1 20); do
    if curl -fsS -H "X-Forwarded-Proto: https" http://127.0.0.1:8000/api/health/ > /dev/null 2>&1; then
        echo "api отвечает"
        curl -fsS http://127.0.0.1:3000 > /dev/null 2>&1 && echo "фронтенд отвечает" || echo "ВНИМАНИЕ: фронтенд молчит"
        echo "готово"
        exit 0
    fi
    sleep 2
done

echo "ОШИБКА: api не поднялся"
systemctl status codecup-api --no-pager --lines=20 || true
exit 1
