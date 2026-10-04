from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from accounts.urls import auth_urlpatterns, user_urlpatterns
from core.views import HealthView

api_urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("auth/", include(auth_urlpatterns)),
    path("users/", include(user_urlpatterns)),
    path("", include("rentals.urls")),
]

if settings.API_DOCS_ENABLED:
    api_urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/", include(api_urlpatterns)),
]

handler404 = "core.exceptions.json_not_found"
handler500 = "core.exceptions.json_server_error"
