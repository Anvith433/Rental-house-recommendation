from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import HouseViewSet, RecommendationView


router = DefaultRouter()

router.register(
    "houses",
    HouseViewSet
)


urlpatterns = router.urls

urlpatterns += [
    path(
        "recommendations/",
        RecommendationView.as_view()
    ),
]