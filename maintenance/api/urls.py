from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BreakdownLogViewSet,  MachineViewSet, TypeViewSet, SupplierViewSet, CategoryViewSet, BrandViewSet, ProblemCategoryViewSet

router = DefaultRouter()
router.register(r'breakdown-logs', BreakdownLogViewSet, basename='breakdownlog')
router.register(r'machines', MachineViewSet, basename='machine')

router.register(r'brand', BrandViewSet, basename='brand')
router.register(r'supplier', SupplierViewSet, basename='supplier')
router.register(r'category', CategoryViewSet, basename='category')
router.register(r'type', TypeViewSet, basename='type')
router.register(r'problem-category', ProblemCategoryViewSet, basename='problem-category')

urlpatterns = [
    path('', include(router.urls)),
]