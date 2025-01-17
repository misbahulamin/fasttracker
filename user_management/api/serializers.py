from django.contrib.auth.models import User, Group
from rest_framework import serializers
from company.models import Company  # Assuming these are in the company app
from ..models import Employee, Department, Designation, DeviceToken
from production.models import Line


# --------------------------
# User Serializer
# --------------------------

class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        """
        Check that the email is unique.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate(self, data):
        """
        Ensure that password and confirm_password match.
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
        validated_data.pop('confirm_password')  # Remove confirm_password as it's not needed
        user = User.objects.create_user(
            username=validated_data['email'],  # Using email as username
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

# --------------------------
# Employee Serializers
# --------------------------

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'name', 'company', 'department', 'mobile',
            'designation', 'employee_id', 'date_of_joining',
        ]
        read_only_fields = ['id', 'user']

# --------------------------
# User Registration Serializer
# --------------------------

class UserRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    designation = serializers.PrimaryKeyRelatedField(queryset=Designation.objects.all())
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = Employee
        fields = [
            'id','user', 'name', 'company', 'department', 'mobile',
            'designation', 'employee_id', 'date_of_joining'
        ]

    def validate_company(self, value):
        if not Company.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Company does not exist.")
        return value

    def validate_department(self, value):
        if not Department.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Department does not exist.")
        return value

    def validate_designation(self, value):
        if not Designation.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Designation does not exist.")
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        employee = Employee.objects.create(user=user, **validated_data)
        return employee

# --------------------------
# Add Employee Serializer
# --------------------------

class AddEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'id', 'name', 'company', 'department', 'mobile',
            'designation', 'employee_id', 'date_of_joining'
        ]

    def validate_company(self, value):
        if not Company.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Company does not exist.")
        return value

    def validate_department(self, value):
        if not Department.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Department does not exist.")
        return value

    def validate_designation(self, value):
        if not Designation.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Designation does not exist.")
        return value

    def validate_line(self, value):
        if not Line.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Line does not exist.")
        return value

    def create(self, validated_data):
        user = None
        employee = Employee.objects.create(user=user, **validated_data)
        return employee

# --------------------------
# User Login Serializer
# --------------------------

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


# --------------------------
# PUsh Notification DeviceToken Serializer
# --------------------------

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token']
        read_only_fields = ['id']

# --------------------------
# User Group Serializer
# --------------------------

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
