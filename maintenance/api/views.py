from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from ..models import BreakdownLog, Machine, Type, Brand, Category, Supplier, ProblemCategory, ProblemCategoryType
from .serializers import BreakdownLogSerializer, MachineSerializer, TypeSerializers, BrandSerializers, CategorySerializers, SupplierSerializers, ProblemCategorySerializers, ProblemCategoryTypeSerializer
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from ..filters import MachineFilter
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from permissions.base_permissions import HasGroupPermission
from rest_framework.exceptions import NotFound
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DurationField
from rest_framework.decorators import action
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncDate
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
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = MachineFilter
    ordering_fields = '__all__'  # Allows ordering on all fields
    ordering = ['id']  
    # permission_classes = [HasGroupPermission]
    search_fields = [
        'machine_id', 'category__name', 'type__name', 'brand__name', 
        'model_number', 'serial_no', 'line__name', 'sequence', 'supplier__name', 
        'purchase_date', 'last_breakdown_start', 'last_repairing_start', 
        'mechanic__name', 'operator__name', 'last_problem', 'status', 
        'company__name', 'line__floor__name'
    ]

    # def get_ordering(self):
    #     ordering = self.request.query_params.get('ordering', None)
    #     if ordering:
    #         # Validate if the ordering field is allowed
    #         allowed_fields = ['purchase_date', 'brand_name', 'categoryname', 'type_name']
    #         if ordering not in allowed_fields:
    #             raise NotFound(f"Ordering by '{ordering}' is not allowed.")
    #         return [ordering]
    #     return super().get_ordering()
    
class MachinePaginationViewSet(ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = MachineFilter
    ordering_fields = '__all__'  # Allows ordering on all fields
    ordering = ['id']  
    pagination_class = MachinePagination
    # permission_classes = [HasGroupPermission]
    search_fields = [
        'machine_id', 'category__name', 'type__name', 'brand__name', 
        'model_number', 'serial_no', 'line__name', 'sequence', 'supplier__name', 
        'purchase_date', 'last_breakdown_start', 'last_repairing_start', 
        'mechanic__name', 'operator__name', 'last_problem', 'status', 
        'company__name', 'line__floor__name'
    ]


    
class BreakdownLogViewSet(ModelViewSet):
    queryset = BreakdownLog.objects.all()
    serializer_class = BreakdownLogSerializer
    # permission_classes = [HasGroupPermission]

    @action(detail=False, methods=["get"], url_path="total-lost-time-per-location")
    def total_lost_time(self, request):
        
        floors = request.query_params.get("floor", "")  # e.g., "1,2"
        line_nos = request.query_params.get("line", "")  # e.g., "3"
        dates = request.query_params.get("date", "")     # e.g., "2025-02-05,2025-02-06"

        floor_list = [f.strip() for f in floors.split(",") if f.strip()] if floors else []
        line_no_list = [l.strip() for l in line_nos.split(",") if l.strip()] if line_nos else []
        date_list = [d.strip() for d in dates.split(",") if d.strip()] if dates else []

        breakdown_queryset = self.get_queryset()

        if floor_list:
            breakdown_queryset = breakdown_queryset.filter(line__floor__id__in=floor_list)
        if line_no_list:
            breakdown_queryset = breakdown_queryset.filter(line__id__in=line_no_list)
        if date_list:
            # Parse each date; collect only valid ones
            parsed_dates = []
            for date_str in date_list:
                parsed_date = parse_date(date_str)
                if parsed_date:
                    parsed_dates.append(parsed_date)
            if parsed_dates:
                breakdown_queryset = breakdown_queryset.filter(breakdown_start__date__in=parsed_dates)

        # Calculate total lost time (stringified)
        total_lost_time = breakdown_queryset.aggregate(total=Sum("lost_time"))["total"]
        formatted_total_lost_time = str(total_lost_time) if total_lost_time else "0:00:00"

        # Machines (filtered by floor/line but NOT date)
        machine_queryset = Machine.objects.all()
        if floor_list:
            machine_queryset = machine_queryset.filter(line__floor__id__in=floor_list)
        if line_no_list:
            machine_queryset = machine_queryset.filter(line__id__in=line_no_list)

        total_machine_count = machine_queryset.count()
        total_active_machines = machine_queryset.filter(status="active").count()
        total_repairing_machines = machine_queryset.filter(status="maintenance").count()
        total_idle_machines = machine_queryset.filter(status="inactive").count()

        # overall avg_time_to_respond for the filtered BreakdownLogs
        # here, "time to respond" = (repairing_start - breakdown_start) and I exclude records with no repairing_start.
        respond_stats = (
            breakdown_queryset
            .exclude(repairing_start__isnull=True)
            .annotate(
                respond_time=ExpressionWrapper(
                    F('repairing_start') - F('breakdown_start'),
                    output_field=DurationField()
                )
            )
            .aggregate(avg_time=Avg('respond_time'))
        )
        overall_avg_respond_time = respond_stats["avg_time"]
        formatted_avg_time_to_respond = str(overall_avg_respond_time) if overall_avg_respond_time else "0:00:00"

        # Summaries

        # summary by Machine (group by machine)
        summary_by_machine_qs = (
            breakdown_queryset
            .values(
                "machine__id",
                "machine__machine_id",
                "machine__status",
                "machine__type__name",
            )
            .annotate(
                breakdowns_count=Count("id"),
                lost_time=Sum("lost_time")
            )
        )
        summary_by_machine_id = []
        for item in summary_by_machine_qs:
            summary_by_machine_id.append({
                "id": item["machine__id"],
                "machine_id": item["machine__machine_id"],
                "status": item["machine__status"],
                "type": item["machine__type__name"] if item["machine__type__name"] else None,
                "breakdowns_count": item["breakdowns_count"],
                "lost_time": str(item["lost_time"]) if item["lost_time"] else "0:00:00",
            })

        # Summary by Type (group by machine type)
        # Also count distinct machines of that type (in the *filtered breakdowns*)
        summary_by_type_qs = (
            breakdown_queryset
            .values("machine__type__id", "machine__type__name")
            .annotate(
                machine_count=Count("machine__id", distinct=True),
                breakdowns_count=Count("id"),
                lost_time=Sum("lost_time"),
            )
        )
        summary_by_type = []
        for item in summary_by_type_qs:
            summary_by_type.append({
                "type": item["machine__type__name"] if item["machine__type__name"] else None,
                "machine_count": item["machine_count"],
                "breakdowns_count": item["breakdowns_count"],
                "lost_time": str(item["lost_time"]) if item["lost_time"] else "0:00:00"
            })

        # Summary by Problem (group by problem_category)
        summary_by_problem_qs = (
            breakdown_queryset
            .values("problem_category__id", "problem_category__name")
            .annotate(
                breakdowns_count=Count("id"),
                lost_time=Sum("lost_time")
            )
        )
        summary_by_problem = []
        for item in summary_by_problem_qs:
            summary_by_problem.append({
                "problem": item["problem_category__name"] if item["problem_category__name"] else None,
                "breakdowns_count": item["breakdowns_count"],
                "lost_time": str(item["lost_time"]) if item["lost_time"] else "0:00:00"
            })

        # Summary by Line (group by line)
        summary_by_line_qs = (
            breakdown_queryset
            .values("line__id", "line__name")
            .annotate(
                breakdowns_count=Count("id"),
                lost_time=Sum("lost_time")
            )
        )
        summary_by_line = []
        for item in summary_by_line_qs:
            summary_by_line.append({
                "id": item["line__id"],
                "line": item["line__name"] if item["line__name"] else None,
                "breakdowns_count": item["breakdowns_count"],
                "lost_time": str(item["lost_time"]) if item["lost_time"] else "0:00:00"
            })

        # Summary by Day (group by date of breakdown_start)
        #    Use TruncDate to group by the date portion
        summary_by_day_qs = (
            breakdown_queryset
            .annotate(date_only=TruncDate("breakdown_start"))
            .values("date_only")
            .annotate(
                breakdowns_count=Count("id"),
                lost_time=Sum("lost_time")
            )
        )
        summary_by_day = []
        for item in summary_by_day_qs:
            summary_by_day.append({
                "date": str(item["date_only"]),  # e.g., "2025-02-05"
                "breakdowns_count": item["breakdowns_count"],
                "lost_time": str(item["lost_time"]) if item["lost_time"] else "0:00:00"
            })

        # Summary by Mechanic (group by mechanic)
        # Also include average time to respond per mechanic
        summary_by_mechanic_qs = (
            breakdown_queryset
            # exclude logs that have no repairing_start so we can compute a response time
            .exclude(repairing_start__isnull=True)
            .annotate(
                respond_time=ExpressionWrapper(
                    F("repairing_start") - F("breakdown_start"),
                    output_field=DurationField()
                )
            )
            .values("mechanic__id")
            .annotate(
                breakdowns_count=Count("id"),
                lost_time=Sum("lost_time"),
                avg_time_to_respond=Avg("respond_time")
            )
        )
        summary_by_mechanic = []
        for item in summary_by_mechanic_qs:
            summary_by_mechanic.append({
                "id": item["mechanic__id"],
                "avg_time_to_respond": str(item["avg_time_to_respond"]) if item["avg_time_to_respond"] else "0:00:00",
                "breakdowns_count": item["breakdowns_count"],
                "lost_time": str(item["lost_time"]) if item["lost_time"] else "0:00:00"
            })

        response_data = {
            "floors": floor_list,
            "line_nos": line_no_list,
            "dates": date_list,
            "total_lost_time": formatted_total_lost_time,
            "total_machine_count": total_machine_count,
            "total_active_machines": total_active_machines,
            "total_repairing_machines": total_repairing_machines,
            "total_idle_machines": total_idle_machines,       
            "avg_time_to_respond": formatted_avg_time_to_respond,

            "summary_by_machine_id": summary_by_machine_id,
            "summary_by_type": summary_by_type,
            "summary_by_problem": summary_by_problem,
            "summary_by_line": summary_by_line,
            "summary_by_day": summary_by_day,
            "summary_by_mechanic": summary_by_mechanic,
        }

        return Response(response_data)

    """
    @action(detail=False, methods=["get"], url_path="total-lost-time-per-location")
    def total_lost_time(self, request):

        floors = request.query_params.get("floor", "")  # Example: "1,2,3"
        line_nos = request.query_params.get("line", "")  # Example: "10,11"
        dates = request.query_params.get("date", "")    # Example: "2025-02-05,2025-02-06"

        floor_list = [f.strip() for f in floors.split(",") if f.strip()] if floors else []
        line_no_list = [l.strip() for l in line_nos.split(",") if l.strip()] if line_nos else []
        date_list = [d.strip() for d in dates.split(",") if d.strip()] if dates else []

        breakdown_queryset = self.get_queryset()

        # Filter by floor
        if floor_list:
            breakdown_queryset = breakdown_queryset.filter(line__floor__id__in=floor_list)

        # Filter by line
        if line_no_list:
            breakdown_queryset = breakdown_queryset.filter(line__id__in=line_no_list)

        # Filter by multiple dates if provided
        if date_list:
            parsed_dates = []
            for date_str in date_list:
                parsed_date = parse_date(date_str)
                if parsed_date:
                    parsed_dates.append(parsed_date)
            if parsed_dates:
                breakdown_queryset = breakdown_queryset.filter(breakdown_start__date__in=parsed_dates)

        
        total_lost_time = breakdown_queryset.aggregate(Sum("lost_time"))["lost_time__sum"]
        formatted_total_lost_time = str(total_lost_time) if total_lost_time else "0:00:00"

        
        machine_queryset = Machine.objects.all()
        
        if floor_list:
            machine_queryset = machine_queryset.filter(line__floor__id__in=floor_list)
        if line_no_list:
            machine_queryset = machine_queryset.filter(line__id__in=line_no_list)

        # 5. Calculate machine stats
        total_machine_count = machine_queryset.count()
        total_active_machines = machine_queryset.filter(status="active").count()
        total_repairing_machines = machine_queryset.filter(status="maintenance").count()
        total_idle_machines = machine_queryset.filter(status="inactive").count()

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
                "floor": machine.line.floor.name if machine.line and machine.line.floor else None,
                "supplier": machine.supplier.name if machine.supplier else None,
            }
            for machine in machine_queryset
        ]

        response_data = {
            "floors": floor_list,
            "line_nos": line_no_list,
            "dates": date_list,
            "total_lost_time": formatted_total_lost_time,
            "total_machine_count": total_machine_count,
            "total_active_machines": total_active_machines,
            "total_repairing_machines": total_repairing_machines,
            "total_idle_machines": total_idle_machines,
            "machines": machine_data,
        }

        return Response(response_data)


    
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
    """
    
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
    # permission_classes = [HasGroupPermission]

class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializers
    # permission_classes = [HasGroupPermission]

class SupplierViewSet(ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializers
    # permission_classes = [HasGroupPermission]



class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializers
    # permission_classes = [HasGroupPermission]

class ProblemCategoryViewSet(ModelViewSet):
    queryset = ProblemCategory.objects.all()
    serializer_class = ProblemCategorySerializers
    # permission_classes = [HasGroupPermission]

class ProblemCategoryTypeViewSet(ModelViewSet):
    queryset = ProblemCategoryType.objects.all()
    serializer_class = ProblemCategoryTypeSerializer
    # permission_classes = [HasGroupPermission]

