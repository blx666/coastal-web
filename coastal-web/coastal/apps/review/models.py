from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder


class Review(models.Model):
    owner = models.ForeignKey(User)
    product = models.ForeignKey(Product)
    order = models.ForeignKey(RentalOrder)
    score = models.PositiveSmallIntegerField()
    content = models.TextField()
