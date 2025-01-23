from django.db import models
from user_management.models import Employee
from company.models import Company
from production.models import Line

class Brand(models.Model):
    name = models.CharField(max_length = 30)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length = 30)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    
class Type(models.Model):
    name = models.CharField(max_length = 30)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length = 30)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    


class Machine(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('broken', 'Broken'),
    ]

    machine_id = models.CharField(max_length=255, unique=True)  # Add MachineID as the primary key
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    type = models.ForeignKey(Type, on_delete=models.CASCADE, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True, null=True)
    model_number = models.CharField(max_length=255, blank=True, null=True)
    serial_no = models.CharField(max_length=255, blank=True, null=True)
    line = models.ForeignKey(Line, on_delete=models.SET_NULL, blank=True, null=True)
    sequence = models.SmallIntegerField(blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE,blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    last_breakdown_start = models.DateTimeField(blank=True, null=True)
    last_repairing_start = models.DateTimeField(blank=True, null=True)
    mechanic = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="mechanic_machine")
    operator = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="operator_machine")
    last_problem = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category} ({self.model_number})"


class ProblemCategoryType(models.Model):
    """Main categories of problems."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class ProblemCategory(models.Model):
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='minor')
    category_type = models.ForeignKey(
        ProblemCategoryType, related_name="categories", on_delete=models.CASCADE
    )
    
    def __str__(self):
        return f"{self.name} ({self.category_type})"


class BreakdownLog(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=True, related_name="machine_breakdowns")
    mechanic = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="mechanic_breakdowns")
    operator = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name="operator_breakdowns")
    problem_category = models.ForeignKey(ProblemCategory, on_delete=models.CASCADE,blank=True, null=True, related_name="breakdown_logs")
    line = models.ForeignKey(Line, on_delete=models.SET_NULL, blank=True, null=True)
    breakdown_start = models.DateTimeField()
    repairing_start = models.DateTimeField(blank=True, null=True)
    lost_time = models.DurationField()
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Breakdown for {self.machine.category} on {self.breakdown_start}"

    class Meta:
        verbose_name = "Breakdown Log"
        verbose_name_plural = "Breakdown Logs"
        ordering = ["-breakdown_start"]