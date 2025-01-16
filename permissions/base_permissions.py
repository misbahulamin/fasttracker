from rest_framework.permissions import BasePermission

# Custom Permission Classes

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.is_authenticated and request.user.employee.designation == 'admin'

class IsSupervisor(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.is_authenticated and request.user.employee.designation == 'supervisor'

class IsMechanic(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.is_authenticated and request.user.employee.designation == 'hr'
    
class IsHR(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.is_authenticated and request.user.employee.designation == 'mechanic'

# Combined Permission Class for OR Logic
class IsAdminOrSupervisorOrMechanic(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.employee.designation in ['admin', 'supervisor', 'mechanic']

# Optional: Separate Combined Permissions
class IsAdminOrMechanic(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.employee.designation in ['admin', 'mechanic']
    
class IsAdminOrHR(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'employee'):
            return False
        return request.user.employee.designation in ['admin', 'hr']
    