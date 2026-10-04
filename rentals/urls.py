from django.urls import path
from rest_framework.routers import DefaultRouter

from accounts.views import AdminUserViewSet

from .views import (
    AdminAnalyticsView,
    AdminInquiryViewSet,
    AdminPropertyViewSet,
    FavoriteDetailView,
    FavoriteIdsView,
    FavoriteListView,
    PreferenceView,
    PropertyViewSet,
    RecommendationHistoryView,
    RecommendationView,
)

router = DefaultRouter()
router.register("properties", PropertyViewSet, basename="property")
# Original endpoint name, kept as an alias for existing clients.
router.register("houses", PropertyViewSet, basename="house")
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("admin/properties", AdminPropertyViewSet, basename="admin-property")
router.register("admin/inquiries", AdminInquiryViewSet, basename="admin-inquiry")

urlpatterns = [
    path("recommendations/", RecommendationView.as_view(), name="recommendations"),
    path(
        "recommendations/history/",
        RecommendationHistoryView.as_view(),
        name="recommendation-history",
    ),
    path("favorites/", FavoriteListView.as_view(), name="favorites"),
    path("favorites/ids/", FavoriteIdsView.as_view(), name="favorite-ids"),
    path("favorites/<int:property_id>/", FavoriteDetailView.as_view(), name="favorite-detail"),
    path("preferences/", PreferenceView.as_view(), name="preferences"),
    path("admin/analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
] + router.urls
