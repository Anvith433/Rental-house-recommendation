"""Request correlation and access logging middleware."""

import logging
import re
import time
import uuid

from django.http import JsonResponse

from .health import health_status

from .request_context import request_id_var, user_id_var

REQUEST_ID_HEADER = "X-Request-ID"
# Accept client-supplied IDs only if they are short and harmless, so they can
# be safely echoed into headers and logs.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

access_logger = logging.getLogger("rentwise.access")


HEALTH_PATH = "/api/health/"


class HealthCheckMiddleware:
    """Answers health probes before host validation and HTTPS redirects.

    Platform probes (Docker, Render, load balancers) call the service by an
    internal address that is deliberately absent from ALLOWED_HOSTS. The
    response carries only up/down information, so serving it for any host is safe.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == HEALTH_PATH and request.method in ("GET", "HEAD"):
            payload, status_code = health_status()
            return JsonResponse(payload, status=status_code)
        return self.get_response(request)


class RequestIDMiddleware:
    """Assigns every request an ID, exposed as ``request.request_id`` and in
    the ``X-Request-ID`` response header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get(REQUEST_ID_HEADER, "")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        request.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response[REQUEST_ID_HEADER] = request_id
        return response


class AccessLogMiddleware:
    """Logs one structured line per request: method, path, status, duration.

    Query strings, headers and bodies are deliberately not logged so tokens and
    passwords can never leak into logs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        user = getattr(request, "user", None)
        user_id = user.pk if user is not None and user.is_authenticated else None
        token = user_id_var.set(user_id)
        try:
            access_logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                },
            )
        finally:
            user_id_var.reset(token)
        return response
