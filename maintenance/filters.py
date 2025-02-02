import django_filters
from .models import Machine

class MachineFilter(django_filters.FilterSet):
    machine_id = django_filters.CharFilter(lookup_expr='icontains', label='Machine ID')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains', label='Category')
    type = django_filters.CharFilter(field_name='type__name', lookup_expr='icontains', label='Type')
    brand = django_filters.CharFilter(field_name='brand__name', lookup_expr='icontains', label='Brand')
    model_number = django_filters.CharFilter(lookup_expr='icontains', label='Model Number')
    serial_no = django_filters.CharFilter(lookup_expr='icontains', label='Serial Number')
    floor = django_filters.CharFilter(field_name='line__floor__name', lookup_expr='icontains', label='Floor Name')
    line = django_filters.CharFilter(field_name='line__name', lookup_expr='icontains', label='Line Name')
    supplier = django_filters.CharFilter(field_name='supplier__name', lookup_expr='icontains', label='Supplier')
    purchase_date = django_filters.DateFilter(lookup_expr='exact', label='Purchase Date')
    last_breakdown_start = django_filters.DateTimeFilter(lookup_expr='exact', label='Last Breakdown Start')
    status = django_filters.ChoiceFilter(choices=Machine.STATUS_CHOICES, label='Status')

    class Meta:
        model = Machine
        fields = ['machine_id', 'category', 'type', 'brand', 'model_number', 'serial_no', 
                  'supplier', 'purchase_date', 'last_breakdown_start', 'status']