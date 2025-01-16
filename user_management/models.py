from django.db import models
from django.contrib.auth.models import User
from company.models import Company

class Department(models.Model):
    name = models.CharField(max_length = 50)
    code = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    
class Designation(models.Model):
    title = models.CharField(max_length = 100)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, null=True, blank=True
    )
    level = models.IntegerField(null=True, blank=True)
    def __str__(self):
        return self.title

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', null=True, blank=True)
    name = models.CharField(max_length=50)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    mobile = models.CharField(max_length=11, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.CharField(max_length=20, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.designation}"
    

class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.token}"