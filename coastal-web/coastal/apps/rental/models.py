from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product


class BlackOutDate(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)


class RentalDateRange(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)


class RentalOrder(models.Model):
    STATUS_CHOICES = (
        ('request', 'Request'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('charge', 'Charge'),
        ('booked', 'Booked'),
        ('check-in', 'Check-In'),
        ('paid', 'Paid Host'),
        ('check-out', 'Check-out'),
        ('finished', 'Finished'),
    )
    CHARGE_UNIT_CHOICES = (
        ('day', 'Day'),
        ('half-day', 'Half-Day'),
        ('hour', 'Hour'),
    )
    number = models.CharField(max_length=32)
    product = models.ForeignKey(Product)
    owner = models.ForeignKey(User, related_name="owner_orders")
    guest = models.ForeignKey(User, related_name="guest_orders")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    rental_unit = models.CharField(max_length=32, choices=CHARGE_UNIT_CHOICES, default='day')
    timezone = models.CharField(max_length=3)
    guest_count = models.PositiveSmallIntegerField()
    sub_total_price = models.FloatField()
    total_price = models.FloatField()
    currency = models.CharField(max_length=3)

    status = models.CharField(max_length=32)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)


class RentalOrderDiscount(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ('w', 'Weekly'),
        ('m', 'Monthly'),
    )
    rental_order = models.ForeignKey(RentalOrder)
    discount_type = models.CharField(max_length=1, choices=DISCOUNT_TYPE_CHOICES)
    discount_rate = models.IntegerField(help_text="The unit is %. e.g. 60 means 60%")


class ApproveEvent(models.Model):
    order = models.ForeignKey(RentalOrder)
    approve = models.BooleanField()
    notes = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class PaymentEvent(models.Model):
    order = models.ForeignKey(RentalOrder)
    customer_token = models.CharField(max_length=128)
    payment_type = models.CharField(max_length=32)
    amount = models.FloatField()
    currency = models.CharField(max_length=3)
    reference = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
