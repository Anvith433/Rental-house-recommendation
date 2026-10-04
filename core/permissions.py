from rest_framework.permissions import SAFE_METHODS, BasePermission


def is_admin_user(user) -> bool:
    return bool(user and user.is_authenticated and user.is_platform_admin)


class IsAdminRole(BasePermission):
    """Only users with the ADMIN role (or superusers)."""

    message = "Administrator privileges are required."

    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrReadOnly(BasePermission):
    """Anyone may read; only administrators may write."""

    message = "Administrator privileges are required."

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_admin_user(request.user)
