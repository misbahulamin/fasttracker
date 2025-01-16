from django.contrib import admin
from .models import Employee, Department, Designation, DeviceToken

class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'get_user_email', 
        'department',
        'designation',
        'company', 
        'mobile', 
        'employee_id', 
        'date_of_joining'
    )

    def get_user_email(self, obj):
        if obj.user:
            return obj.user.email or obj.user.username  # Prefer email, fallback to username
        return "No User"  # Default for employees without a user
    get_user_email.short_description = 'User Email/Username'  # Column header in admin

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')

class DesignationAdmin(admin.ModelAdmin):
    list_display = ('title', 'company')

admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Designation, DesignationAdmin)
admin.site.register(DeviceToken)