from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..models import BreakdownLog, Machine, Type, Brand, Category, Supplier, ProblemCategory
from .serializers import BreakdownLogSerializer, MachineSerializer, TypeSerializers, BrandSerializers, CategorySerializers, SupplierSerializers, ProblemCategorySerializers
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from ..filters import MachineFilter
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from permissions.base_permissions import IsAdmin, IsHR, IsMechanic, IsSupervisor, IsAdminOrSupervisorOrMechanic, IsAdminOrMechanic
from rest_framework.exceptions import NotFound
from django.db.models import Sum
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from rest_framework.exceptions import PermissionDenied

class MachinePagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_size_query_param = 'page_size'  # Allows users to specify the page size via query parameter
    max_page_size = 100  # Maximum number of items per page


class MachineViewSet(ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_class = MachineFilter
    ordering_fields = '__all__'  # Allows ordering on all fields
    ordering = ['id']  # Default ordering (optional)
    pagination_class = MachinePagination
    search_fields = ['machine_id', 'brand__name', 'category__name', 'type__name', 'model_number', 'serial_no', 'location__room']

    # permission_classes = [DjangoModelPermissions]

    def get_ordering(self):
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            # Validate if the ordering field is allowed
            allowed_fields = ['purchase_date', 'brand_name', 'categoryname', 'type_name']
            if ordering not in allowed_fields:
                raise NotFound(f"Ordering by '{ordering}' is not allowed.")
            return [ordering]
        return super().get_ordering()
    
    # def get_queryset(self):
    #     # Check if the user belongs to the "Machine Viewer" group
    #     if not self.request.user.groups.filter(name="Machine-Viewer").exists():
    #         raise PermissionDenied("You do not have permission to view machines.")

    #     # If the user is in the "Machine Viewer" group, return the queryset
    #     return super().get_queryset()
    
    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         # print(f"{self.action.capitalize()} called.")
    #         return [IsAdminOrSupervisorOrMechanic()]
        
    #     if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #         # print(f"{self.action} called.")
    #         return [IsAdminOrMechanic()]  # Adjust as needed
        
    #     return super().get_permissions()


    
class BreakdownLogViewSet(ModelViewSet):
    queryset = BreakdownLog.objects.all()
    serializer_class = BreakdownLogSerializer    

    @action(detail=False, methods=["get"], url_path="total-lost-time-per-location")
    def total_lost_time(self, request):
        # Parse query parameters
        floors = request.query_params.get("floor", "")  # Example: "A,B"
        line_nos = request.query_params.get("line", "")  # Example: "1,2"

        # Split the parameters into lists
        floor_list = floors.split(",") if floors else []
        line_no_list = line_nos.split(",") if line_nos else []

        # Filter the BreakdownLog queryset based on the parameters
        breakdown_queryset = self.get_queryset()
        if floor_list:
            breakdown_queryset = breakdown_queryset.filter(line__floor__id__in=floor_list)
        if line_no_list:
            breakdown_queryset = breakdown_queryset.filter(line__id__in=line_no_list)

        # Calculate the total lost time
        total_lost_time = breakdown_queryset.aggregate(Sum("lost_time"))["lost_time__sum"]

        # Format the total lost time
        formatted_total_lost_time = str(total_lost_time) if total_lost_time else "0:00:00"

        # Filter the Machine queryset based on the parameters
        machine_queryset = Machine.objects.all()
        if floor_list:
            machine_queryset = machine_queryset.filter(line__floor__id__in=floor_list)
        if line_no_list:
            machine_queryset = machine_queryset.filter(line__id__in=line_no_list)

        # Calculate machine stats
        total_machine_count = machine_queryset.count()
        total_active_machines = machine_queryset.filter(status="active").count()
        total_repairing_machines = machine_queryset.filter(status="maintenance").count()
        total_idle_machines = machine_queryset.filter(status="inactive").count()

        # Serialize the machines
        machine_data = [
            {
                "id": machine.id,
                "machine_id": machine.machine_id,
                "model_number": machine.model_number,
                "serial_no": machine.serial_no,
                "purchase_date": machine.purchase_date,
                "last_breakdown_start": machine.last_breakdown_start,
                "status": machine.status,
                "category": machine.category.name if machine.category else None,
                "type": machine.type.name if machine.type else None,
                "brand": machine.brand.name if machine.brand else None,
                "line": machine.line.name if machine.line else None,
                "floor": machine.line.floor.name if machine.line.floor else None,
                "supplier": machine.supplier.name if machine.supplier else None,
            }
            for machine in machine_queryset
        ]

        # Build the response
        response_data = {
            "rooms": floor_list,
            "line_nos": line_no_list,
            "total_lost_time": formatted_total_lost_time,
            "total_machine_count": total_machine_count,
            "total_active_machines": total_active_machines,
            "total_repairing_machines": total_repairing_machines,
            "total_idle_machines": total_idle_machines,
            "machines": machine_data,
        }

        return Response(response_data)
    
    @action(detail=False, methods=["get"], url_path="machines-monitoring")
    def machine_monitoring(self, request):
        machine_id = request.query_params.get("machine_id")
        if not machine_id:
            return Response({"error": "Machine ID is required"}, status=400)

        # Retrieve the machine object based on the provided machine_id
        machine = Machine.objects.filter(machine_id=machine_id).first()
        if not machine:
            return Response({"error": "Machine not found"}, status=404)

        # Get the breakdowns for the specified machine in the last week
        one_week_ago = timezone.now() - timedelta(weeks=1)
        breakdowns_last_week = BreakdownLog.objects.filter(
            machine=machine, breakdown_start__gte=one_week_ago
        )

        # Group lost time by day
        daily_lost_time = defaultdict(timedelta)  # Initialize with timedelta values
        for breakdown in breakdowns_last_week:
            breakdown_date = breakdown.breakdown_start.date()  # Extract date
            daily_lost_time[breakdown_date] += breakdown.lost_time  # Add lost time

        # Format daily lost time into a list of dictionaries
        daily_lost_time_list = [
            {"date": day, "lost-time": str(lost_time)}
            for day, lost_time in sorted(daily_lost_time.items())
        ]

        # Additional Calculations (existing logic remains the same)
        total_lost_time_last_week = breakdowns_last_week.aggregate(
            total_lost_time=Sum("lost_time")
        )["total_lost_time"]

        breakdowns_count_last_week = breakdowns_last_week.count()
        total_active_time_last_week = sum(
            breakdown.lost_time.total_seconds() for breakdown in breakdowns_last_week
        )
        total_week_minutes = 7 * 10 * 60  # 1 week in seconds
        utilization_last_week = 1 - ((total_active_time_last_week / 60) / total_week_minutes) if total_week_minutes > 0 else 0

        mtbf_last_week = (
            timedelta(minutes=(total_week_minutes / breakdowns_count_last_week))
            if breakdowns_count_last_week > 1
            else None
        )

        formatted_total_lost_time_last_week = str(total_lost_time_last_week) if total_lost_time_last_week else "0:00:00"
        formatted_mtbf_last_week = str(mtbf_last_week) if mtbf_last_week else "0:00:00"

        response_data = {
            "id": machine.id,
            "machine_id": machine.machine_id,
            "model_number": machine.model_number,
            "serial_no": machine.serial_no,
            "purchase_date": machine.purchase_date,
            "last_breakdown_start": machine.last_breakdown_start,
            "status": machine.status,
            "category": machine.category.name if machine.category else None,
            "type": machine.type.name if machine.type else None,
            "brand": machine.brand.name if machine.brand else None,
            "line": machine.line.name if machine.line else None,
            "floor": machine.line.floor.name if machine.line.floor else None,
            "supplier": machine.supplier.name if machine.supplier else None,
            "total-lost-time-last-week": formatted_total_lost_time_last_week,
            "utilization-last-week": utilization_last_week,
            "breakdowns-count-last-week": breakdowns_count_last_week,
            "MTBF-last-week": formatted_mtbf_last_week,
            "breakdowns-last-week": daily_lost_time_list,  # Add daily lost time
            # "breakdowns-last-week": [
            #     {
            #         "breakdown-start": breakdown.breakdown_start,
            #         "lost-time": str(breakdown.lost_time),
            #     }
            #     for breakdown in breakdowns_last_week
            # ],
            "lost-time-reasons-last-week": [
                {
                    "problem-category": reason["problem_category__name"],
                    "lost-time": str(reason["total_lost_time"]),
                }
                for reason in breakdowns_last_week.values("problem_category__name")
                .annotate(total_lost_time=Sum("lost_time"))
                .order_by("problem_category__name")
            ],
            
        }

        return Response(response_data)




    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
    #         return [IsAdmin()]  # Adjust as needed   
    #     return super().get_permissions()

class TypeViewSet(ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializers

class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializers

class SupplierViewSet(ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializers



class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializers

class ProblemCategoryViewSet(ModelViewSet):
    queryset = ProblemCategory.objects.all()
    serializer_class = ProblemCategorySerializers

