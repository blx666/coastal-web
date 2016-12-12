from django.db import models
from coastal.apps.product.models import Product

class RentalDateRange(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)