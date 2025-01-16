from django.db import models
from company.models import Company

class Floor(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Optional descriptive name
    company = models.ForeignKey(Company, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.name}"

class Line(models.Model):
    OPERATION_TYPES = [
            ('cutting', 'Cutting'),
            ('sewing', 'Sewing'),
            ('washing', 'Washing'),
            ('finishing', 'Finishing')
        ]
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    operation_type = models.CharField(max_length=50, choices=OPERATION_TYPES)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='production_lines')

    def __str__(self):
        return f"{self.name} (Floor: {self.floor})"

