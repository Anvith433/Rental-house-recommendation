"""Production settings.

Every secret comes from the environment; the process refuses to start if a
required value is missing. Assumes TLS terminates at a reverse proxy that sets
X-Forwarded-Proto.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import DATABASES, jwt_settings
from .env import env_bool, env_int, env_list, env_required, env_str

DEBUG = False

SECRET_KEY = env_required("DJANGO_SECRET_KEY")
SIMPLE_JWT = jwt_settings(SECRET_KEY)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
# Render provides the service's own public hostname; trust it automatically.
if env_str("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(env_str("RENDER_EXTERNAL_HOSTNAME"))
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be set in production.")

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3" and not env_bool(
    "ALLOW_SQLITE_IN_PRODUCTION", False
):
    raise ImproperlyConfigured("Production requires DATABASE_URL pointing at PostgreSQL.")

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]

# Cookies are Secure (HTTPS-only) by default. SECURE_COOKIES=False exists
# solely for running the production stack locally over plain HTTP.
SECURE_COOKIES = env_bool("SECURE_COOKIES", True)
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_HTTPONLY = True
REFRESH_COOKIE_SECURE = SECURE_COOKIES

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
