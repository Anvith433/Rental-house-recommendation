"""Local development settings.

Optimised for a fast feedback loop: DEBUG on, SQLite by default (set
DATABASE_URL to use PostgreSQL), relaxed cookie security for plain HTTP.
"""

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, jwt_settings
from .env import env_list, env_str

DEBUG = True

# A development-only key. Production refuses to start without DJANGO_SECRET_KEY.
SECRET_KEY = env_str("DJANGO_SECRET_KEY") or "dev-only-insecure-key-do-not-use-in-production"
SIMPLE_JWT = jwt_settings(SECRET_KEY)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1", "0.0.0.0"])

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"]
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"]
)

# Local development runs over plain HTTP.
REFRESH_COOKIE_SECURE = False

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
