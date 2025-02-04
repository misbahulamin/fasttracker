from django.db import models
from company.models import Company
from maintenance.models import BreakdownLog

class MachinePart(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("company", "name") 

    def __str__(self):
        return f"{self.name} Price: {self.price} Qty: {self.quantity}"


class PurchaseItem(models.Model):
    """Stores purchased parts and updates stock automatically"""
    invoice = models.CharField(max_length=100)
    part = models.ForeignKey(MachinePart, on_delete=models.CASCADE)
    quantity_purchased = models.PositiveIntegerField()
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("company", "invoice") 

    def save(self, *args, **kwargs):
        """Automatically add purchased quantity to stock"""
        super().save(*args, **kwargs)
        self.part.quantity += self.quantity_purchased
        self.part.save()

    def __str__(self):
        return f"{self.quantity_purchased} x {self.part.name}"


class PartsUsageRecord(models.Model):
    """Tracks parts used for machine breakdown repairs and updates stock"""
    part = models.ForeignKey(MachinePart, on_delete=models.PROTECT)
    quantity_used = models.PositiveIntegerField()
    usage_date = models.DateTimeField(auto_now_add=True)
    mechanic = models.CharField(max_length=255)  # Name of the mechanic
    breakdown = models.ForeignKey(BreakdownLog, on_delete=models.CASCADE)
    remarks = models.TextField(blank=True, null=True)  # Optional notes
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        """Automatically deduct used quantity from stock"""
        if self.quantity_used > self.part.quantity:
            raise ValueError("Not enough stock available!")
        super().save(*args, **kwargs)
        self.part.quantity -= self.quantity_used
        self.part.save()
        
    def __str__(self):
        return f"Used {self.quantity_used} x {self.part.name} on {self.usage_date}"