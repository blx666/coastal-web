from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder
from coastal.apps.message.managers import DialogueManager


class Dialogue(models.Model):
    owner = models.ForeignKey(User, related_name="owner_dialogue")
    guest = models.ForeignKey(User, related_name="guest_dialogue")
    product = models.ForeignKey(Product)
    order = models.ForeignKey(RentalOrder, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    objects = DialogueManager()


class Message(models.Model):
    dialogue = models.ForeignKey(Dialogue)
    sender = models.ForeignKey(User, related_name="sender_dialogue")
    receiver = models.ForeignKey(User, related_name="receiver_dialogue")
    _type = models.CharField(max_length=16, db_column='type')
    content = models.TextField()
    read = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)