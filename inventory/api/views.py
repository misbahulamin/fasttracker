# views.py
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework import status
from ..models import MachinePart, PurchaseItem, PartsUsageRecord
from .serializers import MachinePartSerializer, PurchaseItemSerializer, PartsUsageRecordSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, F
from datetime import datetime

class MachinePartViewSet(viewsets.ModelViewSet):
    queryset = MachinePart.objects.all()
    serializer_class = MachinePartSerializer

class PurchaseItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseItem.objects.all()
    serializer_class = PurchaseItemSerializer

class PartsUsageRecordViewSet(viewsets.ModelViewSet):
    queryset = PartsUsageRecord.objects.all()
    serializer_class = PartsUsageRecordSerializer

    @action(detail=False, methods=['get'])
    def total_cost(self, request):
        line = request.query_params.get('line', None)
        startdate = request.query_params.get('startdate', None)
        enddate = request.query_params.get('enddate', None)

        if not line or not startdate or not enddate:
            return Response({"error": "line, startdate, and enddate are required parameters"}, status=400)

        try:
            startdate = datetime.strptime(startdate, '%Y-%m-%d')
            enddate = datetime.strptime(enddate, '%Y-%m-%d')
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        # Filter PartsUsageRecord based on the breakdown's line and date range
        parts_usage_records = PartsUsageRecord.objects.filter(
            breakdown__line=line,
            breakdown__breakdown_start__gte=startdate,
            breakdown__breakdown_start__lte=enddate
        )

        # Calculate the total cost
        total_cost = parts_usage_records.annotate(
            total_cost=F('quantity_used') * F('part__price')
        ).aggregate(
            total_cost_sum=Sum('total_cost')
        )['total_cost_sum'] or 0

        return Response({"total_cost": total_cost})
    
class BulkCreatePartsUsageView(APIView):
    def post(self, request):
        # Expecting a list of PartsUsageRecord objects in the request data
        serializer = PartsUsageRecordSerializer(data=request.data, many=True)

        if serializer.is_valid():
            try:
                # Save all valid records (model's save() method will handle validation)
                saved_instances = serializer.save()
                # Serialize the saved instances and return the response
                response_serializer = PartsUsageRecordSerializer(saved_instances, many=True)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                # Handle the case where the model's save() method raises a ValueError (e.g., insufficient stock)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Return serializer errors if the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)