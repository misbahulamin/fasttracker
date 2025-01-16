from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LineViewSet, FloorViewSet

router = DefaultRouter()
router.register(r'lines', LineViewSet)
router.register(r'floors', FloorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
