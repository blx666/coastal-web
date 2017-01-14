from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product


class Report(models.Model):
    STATUS_CHOICE = (
        (0, '0'),
        (1, '1'),
    )
    product = models.ForeignKey(Product, related_name='product')
    datetime = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICE, default=0)
    user = models.ForeignKey(User, related_name='report_user')
