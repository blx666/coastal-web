from django.db import models
from coastal.apps.product.models import Product


class BlackOutDate(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)


class RentalDateRange(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)