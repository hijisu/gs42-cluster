"""Django 설정. 모든 값은 환경변수(.env.example 참고)에서 읽는다."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """저장소 루트의 .env를 읽는다. 이미 설정된 환경변수는 덮어쓰지 않는다."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(BASE_DIR.parent / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str = "") -> list[str]:
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


DEBUG = _env_bool("DJANGO_DEBUG", False)
# .env.example 의 예시 값. 운영(DEBUG=false)에서 쓰면 세션·CSRF 서명이 공개된 값에 의존하게 된다.
EXAMPLE_SECRET_KEYS = {"change-me", "insecure-dev-only-key"}

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false")
    SECRET_KEY = "insecure-dev-only-key"
elif not DEBUG and SECRET_KEY in EXAMPLE_SECRET_KEYS:
    raise RuntimeError("DJANGO_SECRET_KEY is still the example value; set a real secret in .env")

ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "corsheaders",
    "rest_framework",
    "accounts",
    "meetings",
    "rooms",
    "reviews",
    "library",
    "notifications",
    "devtools",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "gs42"),
        "USER": os.environ.get("POSTGRES_USER", "gs42"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# 표시 시간대는 Asia/Seoul, DB 저장은 UTC.
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Seoul")
USE_TZ = True
LANGUAGE_CODE = "ko-kr"

AUTH_USER_MODEL = "accounts.User"

# ── 인증 ──
FORTYTWO_UID = os.environ.get("FORTYTWO_UID", "")
FORTYTWO_SECRET = os.environ.get("FORTYTWO_SECRET", "")
FORTYTWO_REDIRECT_URI = os.environ.get(
    "FORTYTWO_REDIRECT_URI", "http://localhost:8000/api/auth/callback"
)
STAFF_INTRA_IDS = _env_list("STAFF_INTRA_IDS")
# 모의 로그인은 DJANGO_DEBUG=true 에서만 허용한다.
MOCK_LOGIN_ENABLED = DEBUG

# ── 웹 푸시(VAPID). 개인키가 없으면 푸시 채널과 구독 API 가 꺼지고 앱 안 알림만 동작한다 ──
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@example.com")

# Django 는 JSON API 만 제공하고 정적 파일은 web(Caddy)이 서빙한다. 표준 설정값만 명시한다
# (테스트용 live_server 가 STATIC_URL 을 요구한다).
STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
CORS_ALLOWED_ORIGINS = [FRONTEND_ORIGIN]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [FRONTEND_ORIGIN]

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# 운영(HTTPS)에서는 Secure 쿠키가 기본이다. http://localhost 로 운영 구성을 검증할 때만
# DJANGO_COOKIE_SECURE=false 로 끈다(일부 브라우저는 http 의 Secure 쿠키를 저장하지 않는다).
COOKIE_SECURE = _env_bool("DJANGO_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_SECURE = COOKIE_SECURE

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.interfaces.authentication.Session401Authentication",
    ],
    "EXCEPTION_HANDLER": "common.interfaces.exceptions.api_exception_handler",
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
}
