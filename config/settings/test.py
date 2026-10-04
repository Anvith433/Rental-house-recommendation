"""Settings for the automated test suite."""

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, jwt_settings
from .env import env_str

SECRET_KEY = "test-only-secret-key-not-used-anywhere-else-0123456789"
SIMPLE_JWT = jwt_settings(SECRET_KEY)

ALLOWED_HOSTS = ["testserver", "localhost"]

# SQLite unless DATABASE_URL is provided (CI can point this at PostgreSQL).
if not env_str("DATABASE_URL"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Fast hashing keeps auth tests quick; never use outside tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Generous limits so ordinary tests are never throttled; throttling itself is
# exercised explicitly in rentals/tests/test_security.py.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        scope: "100000/minute" for scope in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    },
}

REFRESH_COOKIE_SECURE = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"]},
}
