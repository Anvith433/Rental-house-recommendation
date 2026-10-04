# Backend image: Django + Gunicorn, run as an unprivileged user.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY manage.py ./
COPY config ./config
COPY core ./core
COPY accounts ./accounts
COPY rentals ./rentals
COPY docker/entrypoint.sh /entrypoint.sh

RUN useradd --system --uid 10001 --home /app rentwise \
    && mkdir -p /app/staticfiles \
    && chown -R rentwise /app/staticfiles \
    && chmod +x /entrypoint.sh

USER rentwise
# Listens on $PORT when the host provides one (Render sets 10000), else 8000.
ENV PORT=8000 \
    WEB_CONCURRENCY=3
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/api/health/', timeout=4).status == 200 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
# Shell form so $PORT expands; gunicorn reads its worker count from WEB_CONCURRENCY.
CMD exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT}" --access-logfile - --forwarded-allow-ips "*"
