from rest_framework.routers import DefaultRouter

from .views import HouseViewSet


router = DefaultRouter()

router.register(
    "houses",
    HouseViewSet
)

urlpatterns = router.urls