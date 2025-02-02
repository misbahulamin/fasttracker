from rest_framework import viewsets
from ..models import Line, Floor
from .serializers import LineSerializer, FloorSerializer
from permissions.base_permissions import HasGroupPermission

class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.select_related('floor').all()
    serializer_class = LineSerializer
    # permission_classes = [HasGroupPermission]

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    # permission_classes = [HasGroupPermission]
