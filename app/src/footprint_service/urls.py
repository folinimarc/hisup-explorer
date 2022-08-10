from django.urls import path, include
from footprint_service import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"footprints", views.FootprintViewSet)

urlpatterns = [
    path("", views.ExplorerView.as_view()),
    path("api/", include(router.urls)),
]
