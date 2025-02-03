from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect

from ..models import Employee, Department, Designation, DeviceToken, Company
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    AddEmployeeSerializer,
    DepartmentSerializer,
    DesignationSerializer,
    DeviceTokenSerializer,
    GroupSerializer,
    EmployeeSerializer,
    UserSerializer
)
from permissions.base_permissions import HasGroupPermission


# -----------------------------------------------------
# Registration View
# -----------------------------------------------------
class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    # permission_classes = [HasGroupPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "User registered successfully! Please login.",
                    "redirect_url": "/login/"
                }, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def get(self, request, *args, **kwargs):
    #     """
    #     Get data for dropdown: companies, departments, and designations
    #     """
    #     companies = Company.objects.all().values('id', 'name')
    #     departments = Department.objects.all().values('id', 'name')
    #     designations = Designation.objects.all().values('id', 'title')

    #     return Response(
    #         {
    #             "companies": list(companies),
    #             "departments": list(departments),
    #             "designations": list(designations),
    #         },
    #         status=status.HTTP_200_OK
    #     )


# -----------------------------------------------------
# Add Employee Viewset
# -----------------------------------------------------
class AddEmployeeViewset(ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = AddEmployeeSerializer
    # permission_classes = [HasGroupPermission]


# -----------------------------------------------------
# Login View
# -----------------------------------------------------
class UserLoginApiView(APIView):
    # permission_classes = [AllowAny]  # Adjust as needed

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(username=email, password=password)
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                login(request, user)
                return Response(
                    {
                        'token': token.key,
                        'user_id': user.id,
                        'message': "Login successful. Redirecting to home.",
                        'redirect_url': "/home/"
                    }, 
                    status=status.HTTP_200_OK
                )
            return Response(
                {'error': "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------------------------------
# List All Users
# -----------------------------------------------------
class UserListView(APIView):
    serializer_class = UserSerializer
    # permission_classes = [HasGroupPermission]

    def get(self, request):
        """
        Retrieve a list of all Users in the system.
        """
        users = User.objects.all()
        data = [
            {"id": user.id, "email": user.email, "username": user.username}
            for user in users
        ]
        return Response(data, status=status.HTTP_200_OK)


# -----------------------------------------------------
# List All Employees
# -----------------------------------------------------

class EmployeeListAPIView(APIView):
    serializer_class = EmployeeSerializer
    model = Employee
    # permission_classes = [HasGroupPermission]

    def get(self, request, id=None):
        """
        Retrieve a list of all Employees or a specific Employee by ID.
        """
        if id:
            try:
                # Retrieve a specific employee by ID
                employee = Employee.objects.get(id=id)
            except Employee.DoesNotExist:
                return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Serialize and return the specific employee
            serializer = UserRegistrationSerializer(employee)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            # Retrieve all employees
            employees = Employee.objects.all()
            serializer = UserRegistrationSerializer(employees, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id=None):
        """
        Delete a specific Employee by ID.
        """
        if id:
            try:
                employee = Employee.objects.get(id=id)
            except Employee.DoesNotExist:
                return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Delete the employee
            employee.delete()
            return Response({"detail": "Employee deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        
        return Response({"detail": "ID is required to delete an employee."}, status=status.HTTP_400_BAD_REQUEST)



# -----------------------------------------------------
# Logout View
# -----------------------------------------------------
class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Logs out the current user by deleting their auth token.
        """
        request.user.auth_token.delete()
        logout(request)
        return Response({'success': "Logout successful"}, status=status.HTTP_200_OK)



# -----------------------------------------------------
# Department CRUD ViewSet
# -----------------------------------------------------
class DepartmentViewSet(ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    # permission_classes = [HasGroupPermission]


# -----------------------------------------------------
# Designation CRUD ViewSet
# -----------------------------------------------------
class DesignationViewSet(ModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    # permission_classes = [HasGroupPermission]

# -----------------------------------------------------
# Push Notification DeviceToken CRUD ViewSet
# -----------------------------------------------------

class DeviceTokenViewSet(ModelViewSet):
    queryset = DeviceToken.objects.all()
    serializer_class = DeviceTokenSerializer
    # permission_classes = [HasGroupPermission]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# -----------------------------------------------------
# Group ViewSet
# -----------------------------------------------------
class GroupViewSet(ReadOnlyModelViewSet):
    """
    Model View Set for Group
    """
    queryset = Group.objects.all()  # Query all groups
    serializer_class = GroupSerializer
    # permission_classes = [HasGroupPermission]
    

# -----------------------------------------------------
# Employee Name & Basic Info View
# -----------------------------------------------------
class EmployeeNameAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves the currently logged-in user's Employee profile
        (name, designation, department, company).
        """
        try:
            employee = request.user.employee
            return Response({
                'name': employee.name,
                'designation': employee.designation.title if employee.designation else None,
                'department': employee.department.name if employee.department else None,
                'company': employee.company.name if employee.company else None
            }, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)
