# serializers.py
from rest_framework import serializers
from ..models import MachinePart, PurchaseItem, PartsUsageRecord

class MachinePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachinePart
        fields = '__all__'

class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = '__all__'

class PartsUsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartsUsageRecord
        fields = '__all__'