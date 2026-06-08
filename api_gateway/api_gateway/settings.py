import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-api-gateway-local"
DEBUG = True
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if os.getenv("DJANGO_ALLOWED_HOSTS") else []

INSTALLED_APPS = [
    "gateway",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

APPEND_SLASH = False
ROOT_URLCONF = "api_gateway.urls"

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

WSGI_APPLICATION = "api_gateway.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

if os.getenv("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GATEWAY_TIMEOUT_SECONDS = 5
GATEWAY_RATE_LIMIT_PER_MINUTE = 120
GATEWAY_SERVICE_URLS = {
    "users": os.getenv("USERS_SERVICE_URL", "http://localhost:8001"),
    "staff": os.getenv("STAFF_SERVICE_URL", "http://localhost:8002"),
    "products": os.getenv("PRODUCTS_SERVICE_URL", "http://localhost:8003"),
    "cart": os.getenv("CART_SERVICE_URL", "http://localhost:8004"),
    "orders": os.getenv("ORDERS_SERVICE_URL", "http://localhost:8005"),
    "payments": os.getenv("PAYMENTS_SERVICE_URL", "http://localhost:8006"),
    "shipping": os.getenv("SHIPPING_SERVICE_URL", "http://localhost:8007"),
    "ai": os.getenv("AI_SERVICE_URL", "http://localhost:8008"),
    "comments": os.getenv("COMMENTS_SERVICE_URL", "http://localhost:8009"),
}
