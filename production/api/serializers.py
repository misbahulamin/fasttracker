from rest_framework import serializers
from ..models import Line, Floor

class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'

class LineSerializer(serializers.ModelSerializer):
    floor = FloorSerializer()  # Nested representation

    class Meta:
        model = Line
        fields = ['id', 'name', 'description', 'operation_type', 'floor']