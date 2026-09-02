"""Настройки, общие для всех окружений."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.common",
    "apps.users",
    "apps.contests",
    "apps.submissions",
    "apps.payments",
    "apps.screening",
    "apps.telegrambot",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Интерфейс и контент проекта — только на русском.
LANGUAGE_CODE = "ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.users.authentication.CookieJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "auth_start": "10/min",
        "auth_status": "120/min",
    },
}

AUTH_USER_MODEL = "users.User"

# Access-кука живёт долго намеренно. Обновлять её через /api/auth/refresh/
# некому: refresh-кука ограничена путём /api/auth/ на домене API, поэтому до
# сервера Next.js, который рендерит страницы, она вообще не доходит. Пока
# access жил 15 минут, пользователь становился гостем через четверть часа —
# при живой refresh-куке на две недели.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- Куки сессии ------------------------------------------------------------
AUTH_COOKIE_ACCESS_NAME = "cc_access"
AUTH_COOKIE_REFRESH_NAME = "cc_refresh"
# Refresh-кука нужна только эндпоинтам авторизации, поэтому её путь узкий.
AUTH_COOKIE_REFRESH_PATH = "/api/auth/"
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_DOMAIN = env("AUTH_COOKIE_DOMAIN", default=None)

# --- Telegram ---------------------------------------------------------------
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_BOT_USERNAME = env("TELEGRAM_BOT_USERNAME", default="")
TELEGRAM_WEBHOOK_SECRET = env("TELEGRAM_WEBHOOK_SECRET", default="")
TELEGRAM_API_URL = "https://api.telegram.org"
TELEGRAM_REQUEST_TIMEOUT = 10
# Столько живёт ссылка для входа; на экране входа это состояние «ссылка устарела».
TELEGRAM_AUTH_TOKEN_TTL = env.int("TELEGRAM_AUTH_TOKEN_TTL", default=300)

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# --- Оплата участия ---------------------------------------------------------
# Реквизиты общие для всех платных контестов; меняются через .env без правки кода.
# В .env перенос строки записывается как \n — разворачиваем его, иначе
# многострочные реквизиты слиплись бы в одну строку.
PAYMENT_REQUISITES = env(
    "PAYMENT_REQUISITES",
    default="Реквизиты для оплаты пока не заданы. Напишите администратору.",
).replace("\\n", "\n")
# Чеки уходят этому администратору. Ищем по @username, а не по числовому id:
# аккаунт может быть пересоздан, username остаётся прежним.
TELEGRAM_ADMIN_USERNAME = env("TELEGRAM_ADMIN_USERNAME", default="AmiriCode")
# Что принимаем как чек.
RECEIPT_MAX_BYTES = env.int("RECEIPT_MAX_BYTES", default=10 * 1024 * 1024)
# --- Проверка присланных репозиториев ---------------------------------------
# Без токена GitHub даёт 60 запросов в час на IP — на контест этого не хватит.
GITHUB_TOKEN = env("GITHUB_TOKEN", default="")
GITHUB_REQUEST_TIMEOUT = env.int("GITHUB_REQUEST_TIMEOUT", default=20)
# Архивы больше этого не качаем: проверка не должна съедать диск и время.
SCREENING_MAX_TARBALL_BYTES = env.int("SCREENING_MAX_TARBALL_BYTES", default=60 * 1024 * 1024)

RECEIPT_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "application/pdf"]

SPECTACULAR_SETTINGS = {
    "TITLE": "CodeCup.tech API",
    "DESCRIPTION": "API платформы контестов для разработчиков.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # Поле status есть и у контеста, и у заявки — без явных имён схема
    # выдаёт что-то вроде Status35aEnum, и типы фронтенда становятся нечитаемыми.
    "ENUM_NAME_OVERRIDES": {
        "ContestStatusEnum": "apps.contests.models.ContestStatus.choices",
        "ContestStateEnum": "apps.contests.models.ContestState.choices",
        "SubmissionStatusEnum": "apps.submissions.models.SubmissionStatus.choices",
        "DisplayStatusEnum": "apps.submissions.models.DisplayStatus.choices",
        "PaymentStatusEnum": "apps.payments.models.PaymentStatus.choices",
        "CurrencyEnum": "apps.contests.models.Currency.choices",
    },
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
# Фронтенд получает JWT в httpOnly-куках, поэтому запросы идут с credentials.
CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        # httpx логирует полный URL запроса, а токен бота — часть пути
        # (/bot<TOKEN>/getMe). На уровне INFO он утекал бы в каждый лог-файл.
        "httpx": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        "httpcore": {"level": "WARNING", "handlers": ["console"], "propagate": False},
    },
}
