# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MachinePartViewSet, PurchaseItemViewSet, PartsUsageRecordViewSet, BulkCreatePartsUsageView

router = DefaultRouter()
router.register(r'machineparts', MachinePartViewSet)
router.register(r'purchaseitems', PurchaseItemViewSet)
router.register(r'partsusagerecords', PartsUsageRecordViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('bulk-create-parts-usage/', BulkCreatePartsUsageView.as_view(), name='bulk-create-parts-usage'),
]