from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmployeeNameAPIView, UserRegistrationView, EmployeeListAPIView, UserLoginApiView, UserLogoutView, UserListView, DepartmentViewSet, DesignationViewSet, AddEmployeeViewset, GroupViewSet


router = DefaultRouter()
router.register(r'department', DepartmentViewSet, basename='department')
router.register(r'designation', DesignationViewSet, basename='designation')
router.register(r'add-employee', AddEmployeeViewset, basename='add-employee')

router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),  # Include router URLs
    path('register/', UserRegistrationView.as_view(), name='register'),  # Add a non-viewset view
    path('login/', UserLoginApiView.as_view(), name='login'),
    path('employee-list/', EmployeeListAPIView.as_view(), name='employee-list'),
    path('employee-list/<int:id>/', EmployeeListAPIView.as_view(), name='specific-employee'),
    path('user-list/', UserListView.as_view(), name='user-list'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('employee-details/', EmployeeNameAPIView.as_view(), name='employee-details'),
]