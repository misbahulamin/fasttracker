from rest_framework import viewsets
from ..models import Line, Floor
from .serializers import LineSerializer, FloorSerializer

class LineViewSet(viewsets.ModelViewSet):
    queryset = Line.objects.select_related('floor').all()
    serializer_class = LineSerializer

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
