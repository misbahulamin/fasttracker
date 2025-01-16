from rest_framework import serializers
from maintenance.models import BreakdownLog
from ..models import Machine, Type, Brand, Category, Supplier, ProblemCategory

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'


class BreakdownLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BreakdownLog
        fields = '__all__'


class BrandSerializers(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

class TypeSerializers(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'

class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class SupplierSerializers(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class ProblemCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = ProblemCategory
        fields = '__all__'