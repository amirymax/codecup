PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help venv install up down logs psql migrate migrations run bot shell superuser schema front front-install front-build front-lint prod-build prod-up prod-logs prod-check test lint format check reset-db

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

venv: ## Создать виртуальное окружение
	python3 -m venv .venv

install: venv ## Установить зависимости для разработки
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements/dev.txt

up: ## Поднять Postgres в Docker
	docker compose up -d
	@printf "Ожидание готовности Postgres"
	@until docker compose exec -T postgres pg_isready -q 2>/dev/null; do printf "."; sleep 1; done; echo " готов"

down: ## Остановить Postgres
	docker compose down

logs: ## Логи Postgres
	docker compose logs -f postgres

psql: ## Открыть psql внутри контейнера
	docker compose exec postgres psql -U $${POSTGRES_USER:-codecup} -d $${POSTGRES_DB:-codecup}

reset-db: ## Удалить базу вместе с данными и поднять заново
	docker compose down -v
	$(MAKE) up
	$(MAKE) migrate

migrations: ## Создать миграции
	$(PY) manage.py makemigrations

migrate: ## Применить миграции
	$(PY) manage.py migrate

run: ## Запустить сервер разработки на :8000
	$(PY) manage.py runserver 0.0.0.0:8000

bot: ## Запустить Telegram-бота (длинный опрос)
	$(PY) manage.py codebot

shell: ## Django shell
	$(PY) manage.py shell

superuser: ## Создать администратора
	$(PY) manage.py createsuperuser

schema: ## Обновить схему OpenAPI и типы для фронтенда
	$(PY) manage.py spectacular --format openapi-json --file frontend/src/lib/api/openapi.json --fail-on-warn
	npx --yes openapi-typescript@7 frontend/src/lib/api/openapi.json -o frontend/src/lib/api/schema.ts

front-install: ## Установить зависимости фронтенда
	cd frontend && npm install

front: ## Запустить фронтенд на :3000
	cd frontend && npm run dev

front-build: ## Собрать фронтенд
	cd frontend && npm run build

front-lint: ## Проверить фронтенд
	cd frontend && npm run lint

prod-build: ## Собрать продакшн-образы
	docker compose -f docker-compose.prod.yml build

prod-up: ## Поднять продакшн локально (нужен .env.prod)
	docker compose -f docker-compose.prod.yml up -d

prod-logs: ## Логи продакшна
	docker compose -f docker-compose.prod.yml logs -f

prod-check: ## Проверить настройки безопасности
	$(PY) manage.py check --deploy --settings=config.settings.production

test: ## Прогнать тесты
	.venv/bin/pytest

lint: ## Проверить стиль
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format: ## Отформатировать код
	.venv/bin/ruff check --fix .
	.venv/bin/ruff format .

check: lint test front-lint front-build ## Все проверки: backend и фронтенд
