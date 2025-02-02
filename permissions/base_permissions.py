# from rest_framework.permissions import BasePermission, SAFE_METHODS
# from django.contrib.auth.models import Group, Permission


# class HasGroupPermission(BasePermission):

#     def has_permission(self, request, view):
#         if request.user.is_superuser:
#             return True

#         model_cls = getattr(view, 'queryset', None)
#         if model_cls is None:
#             return False  

#         model_cls = model_cls.model  

#         # Get model metadata
#         app_label = model_cls._meta.app_label
#         model_name = model_cls._meta.model_name

#         # Action-to-permission codename mapping
#         action_to_codename = {
#             'list': 'view',
#             'retrieve': 'view',
#             'create': 'add',
#             'update': 'change',
#             'partial_update': 'change',
#             'destroy': 'delete',
#         }

#         action = view.action
#         print(f"Has: {action}") 
#         if action is None:
#             return False 
        
#         codename = action_to_codename.get(action, None)
#         # if codename is None:
#         #     return False
#          # Handle custom actions by checking HTTP method
#         if codename is None:
#             if request.method in SAFE_METHODS:
#                 codename = 'view'
#             elif request.method == 'POST':
#                 codename = 'add'
#             elif request.method in ['PUT', 'PATCH']:
#                 codename = 'change'
#             elif request.method == 'DELETE':
#                 codename = 'delete'
#             elif request.method == 'GET':
#                 codename = 'view'
#             else:
#                 return False  # Unsupported method
        
#         permission_codename = f"{codename}_{model_name}"

#         # Check if the user has the required permission
#         user_groups = request.user.groups.all()
#         group_permissions = Permission.objects.filter(group__in=user_groups)
#         user_permissions = group_permissions.values_list('codename', flat=True)
#         print(user_permissions)
#         # If the user has the required permission, allow access
#         if permission_codename in user_permissions:
#             print(permission_codename)
#             return True

#         # Deny access if no matching permission found
#         return False
    


from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured


class HasGroupPermission(BasePermission):

    
    action_to_codename = {
        'list': 'view',
        'retrieve': 'view',
        'create': 'add',
        'update': 'change',
        'partial_update': 'change',
        'destroy': 'delete',
    }

    method_to_codename = {
        'GET': 'view',
        'HEAD': 'view',
        'OPTIONS': 'view',
        'POST': 'add',
        'PUT': 'change',
        'PATCH': 'change',
        'DELETE': 'delete',
    }

    def has_permission(self, request, view):
        
        if request.user.is_superuser:
            return True

        
        model_cls = self._get_model_class(view)
        if not model_cls:
            return False

        codename = self._get_required_codename(view, request)

        if not codename:
            return False

        permission_codename = f"{codename}_{model_cls._meta.model_name}"

        user_permissions = self._get_user_permissions(request.user)
        return permission_codename in user_permissions

    def _get_model_class(self, view):
        
        queryset = getattr(view, 'queryset', None)
        if queryset is not None:
            if hasattr(queryset, 'model'):
                return queryset.model

        if hasattr(view, 'get_queryset') and callable(view.get_queryset):
            try:
                qs = view.get_queryset()  
                if hasattr(qs, 'model'):
                    return qs.model
            except Exception:
                pass  

        serializer_class = getattr(view, 'serializer_class', None)
        if serializer_class and hasattr(serializer_class, 'Meta'):
            meta = getattr(serializer_class, 'Meta', None)
            if meta and hasattr(meta, 'model'):
                return meta.model

        # Could also store an attribute on the view, e.g. `model = SomeModel`
        # if you want a fallback.
        # model_cls = getattr(view, 'model', None)
        # if model_cls:
        #     return model_cls

        return None

    def _get_required_codename(self, view, request):

        # DRF ViewSets have `view.action` (e.g. "list", "create", "retrieve", etc.)
        action = getattr(view, 'action', None)
        if action and action in self.action_to_codename:
            return self.action_to_codename[action]

        # If action is not found, fallback to method-based
        return self.method_to_codename.get(request.method)

    def _get_user_permissions(self, user):
        user_groups = user.groups.all()
        group_permissions = Permission.objects.filter(group__in=user_groups)
        return set(group_permissions.values_list('codename', flat=True))
