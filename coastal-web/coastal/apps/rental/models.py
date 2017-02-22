import math
from django.utils.functional import cached_property
from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.currency.utils import price_display
from coastal.apps.product.models import Product
from coastal.apps.rental.managers import RentalOrderManager


class BlackOutDate(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)


class RentalOrder(models.Model):
    STATUS_CHOICES = (
        ('request', 'Unconfirmed'),  # The order need to be confirmed by host
        ('approved', 'Approved'),  # The order has been confirmed by host
        ('declined', 'Declined'),  # The order has been declined by host
        ('invalid', 'Invalid'),  # The order did not be handle within 24 hours
        ('charge', 'Unpaid'),  # The order need to be paid for by guest
        ('booked', 'In Transaction'),  # Booked successfully
        ('check-in', 'In Transaction'),  # Guest has been checked in (auto set by system)
        ('paid', 'In Transaction'),  # Pay host the rent (auto set by system)
        ('check-out', 'In Transaction'),  # Guest has been checked out (auto set by system)
        ('finished', 'Finished'),
    )
    END_STATUS_LIST = ['declined', 'invalid', 'finished']
    CHARGE_UNIT_CHOICES = (
        ('day', 'Day'),
        ('half-day', 'Half-Day'),
        ('hour', 'Hour'),
        ('week', 'Week'),
    )
    number = models.CharField(max_length=32, unique=True)
    product = models.ForeignKey(Product)
    owner = models.ForeignKey(User, related_name="owner_orders")
    guest = models.ForeignKey(User, related_name="guest_orders")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    rental_unit = models.CharField(max_length=32, choices=CHARGE_UNIT_CHOICES, default='day')
    timezone = models.CharField(max_length=100)
    guest_count = models.PositiveSmallIntegerField()
    sub_total_price = models.FloatField()
    total_price = models.FloatField()
    total_price_usd = models.FloatField()
    currency = models.CharField(max_length=3)
    currency_rate = models.FloatField()
    coastal_dollar = models.FloatField(null=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES)

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = RentalOrderManager()

    def get_total_price_display(self):
        return price_display(self.total_price, self.currency)

    @cached_property
    def time_length(self):
        _unit_mapping = {
            'day': 24,
            'half-day': 6,
            'hour': 1,
            'week': 24 * 7,
        }
        return math.ceil(
            (self.end_datetime - self.start_datetime).total_seconds() / 3600 / _unit_mapping[self.rental_unit])

    def get_time_length_display(self):
        time_length = self.time_length
        return (time_length > 1 and '%s %ss' or '%s %s') % (
            time_length, self.get_rental_unit_display())


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
    TYPE_CHOICES = (
        ('stripe', 'Stripe'),
        ('coastal', 'Coastal Dollar'),
    )
    order = models.ForeignKey(RentalOrder)
    payment_type = models.CharField(max_length=32)
    amount = models.FloatField()
    stripe_amount = models.FloatField(null=True)
    currency = models.CharField(max_length=3)
    reference = models.CharField(max_length=128, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class RentalOutDate(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
