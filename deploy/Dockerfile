# Backend: Django + gunicorn.
# Postgres в этот образ не входит — в продакшне база стоит на сервере.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# libpq нужен psycopg, curl — healthcheck в compose.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/prod.txt

COPY manage.py ./
COPY config/ config/
COPY apps/ apps/

# Работаем не от root.
RUN useradd --system --create-home --uid 1001 codecup \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R codecup:codecup /app
USER codecup

# Статику собираем на этапе сборки: в рантайме файловая система только читается.
RUN DJANGO_SECRET_KEY=build-only \
    DATABASE_URL=postgres://build:build@localhost/build \
    DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
