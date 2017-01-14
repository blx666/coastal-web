from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.validators import validate_comma_separated_integer_list
from coastal.apps.product.models import Product
from coastal.apps.sale.managers import SaleOfferManager


class SaleOffer(models.Model):
    STATUS_CHOICES = (
        ('request', 'Unconfirmed'),  # The offer need to be confirmed by host
        ('approved', 'Approved'),  # The offer has been confirmed by host
        ('declined', 'Declined'),  # The offer has been declined by host
        ('invalid', 'Invalid'),  # The offer did not be handle within 24 hours
        ('charge', 'Unpaid'),  # The offer need to be paid for by guest
        ('paid', 'In Transaction'),  # Pay owner
        ('finished', 'Finished'),
    )

    number = models.CharField(max_length=32, unique=True)
    product = models.ForeignKey(Product)
    owner = models.ForeignKey(User, related_name='owner_offers')
    guest = models.ForeignKey(User, related_name='guest_offers')
    price = models.PositiveIntegerField()
    conditions = models.CharField(max_length=30, blank=True, validators=[validate_comma_separated_integer_list])

    status = models.CharField(max_length=32, choices=STATUS_CHOICES)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = SaleOfferManager()
