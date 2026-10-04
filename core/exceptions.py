"""Consistent API error responses.

Every error leaves the API in one shape::

    {"error": {"code": "INVALID_REQUEST", "message": "...", "details": {...}}}

Unexpected exceptions are logged with their traceback server-side and returned
as a generic 500 so internals (SQL, paths, settings) never reach clients.
"""

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("rentwise.errors")

_CODE_BY_EXCEPTION = (
    (exceptions.ParseError, "MALFORMED_REQUEST"),
    (exceptions.ValidationError, "INVALID_REQUEST"),
    (exceptions.NotAuthenticated, "NOT_AUTHENTICATED"),
    (exceptions.AuthenticationFailed, "AUTHENTICATION_FAILED"),
    (exceptions.PermissionDenied, "PERMISSION_DENIED"),
    (exceptions.NotFound, "NOT_FOUND"),
    (exceptions.MethodNotAllowed, "METHOD_NOT_ALLOWED"),
    (exceptions.NotAcceptable, "NOT_ACCEPTABLE"),
    (exceptions.UnsupportedMediaType, "UNSUPPORTED_MEDIA_TYPE"),
    (exceptions.Throttled, "RATE_LIMITED"),
)


def error_payload(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def _first_message(detail) -> str:
    """Flatten DRF's nested error structure into one readable sentence."""
    if isinstance(detail, dict):
        for field, value in detail.items():
            message = _first_message(value)
            if field in ("non_field_errors", "detail"):
                return message
            return f"{field}: {message}"
        return "Invalid request."
    if isinstance(detail, list):
        return _first_message(detail[0]) if detail else "Invalid request."
    return str(detail)


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, context)

    if response is None:
        view = context.get("view")
        logger.exception(
            "unhandled API exception", extra={"view": view.__class__.__name__ if view else None}
        )
        return Response(
            error_payload("INTERNAL_ERROR", "An unexpected error occurred."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = next(
        (name for exc_class, name in _CODE_BY_EXCEPTION if isinstance(exc, exc_class)),
        "ERROR",
    )
    detail = response.data
    details = detail if isinstance(exc, exceptions.ValidationError) else {}
    if isinstance(details, list):
        details = {"non_field_errors": details}

    payload = error_payload(code, _first_message(detail), details)
    if isinstance(exc, exceptions.Throttled) and exc.wait is not None:
        payload["error"]["details"] = {"retry_after_seconds": int(exc.wait)}

    response.data = payload
    return response


def json_bad_request(request, exception=None):
    return JsonResponse(error_payload("BAD_REQUEST", "Bad request."), status=400)


def json_not_found(request, exception=None):
    return JsonResponse(error_payload("NOT_FOUND", "Not found."), status=404)


def json_server_error(request):
    return JsonResponse(
        error_payload("INTERNAL_ERROR", "An unexpected error occurred."), status=500
    )
