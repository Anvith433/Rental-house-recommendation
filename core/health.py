"""Health status shared by the health endpoint and the health-check middleware."""

from django.db import connection


def health_status() -> tuple[dict, int]:
    """Return the public health payload and HTTP status. Reveals nothing beyond up/down."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        database = "ok"
    except Exception:  # noqa: BLE001 - report, never raise, from a probe
        database = "unavailable"
    healthy = database == "ok"
    return {"status": "ok" if healthy else "degraded", "database": database}, 200 if healthy else 503
