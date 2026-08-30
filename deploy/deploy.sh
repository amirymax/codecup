#!/usr/bin/env bash
# Выкатка новой версии. Запускать из каталога проекта на сервере.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Забираю изменения"
git pull --ff-only

echo "==> Собираю образы"
docker compose -f docker-compose.prod.yml build

echo "==> Применяю миграции"
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

echo "==> Перезапускаю сервисы"
docker compose -f docker-compose.prod.yml up -d

echo "==> Жду готовности backend"
for _ in $(seq 1 30); do
    if docker compose -f docker-compose.prod.yml exec -T backend \
        curl -fs http://localhost:8000/api/health/ > /dev/null 2>&1; then
        echo "готово"
        exit 0
    fi
    sleep 2
done

echo "ОШИБКА: backend не отвечает, показываю логи"
docker compose -f docker-compose.prod.yml logs --tail=50 backend
exit 1
