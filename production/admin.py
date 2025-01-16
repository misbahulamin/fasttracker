from django.contrib import admin
from .models import Floor, Line

# Admin for Floor model
@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Display the 'name' field in the list view
    search_fields = ('name',)  # Enable searching by 'name'
    list_filter = ('name',)  # Add a filter by 'name' (if you have multiple floors)

# Admin for Line model
@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ('name', 'operation_type', 'floor', 'description')  # Fields to display in the list view
    search_fields = ('name', 'operation_type')  # Enable searching by 'name' and 'operation_type'
    list_filter = ('operation_type', 'floor')  # Add filters for 'operation_type' and 'floor'
    ordering = ('floor', 'name')  # Default ordering: first by 'floor', then by 'name'

