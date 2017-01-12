from django.contrib.gis.db import models
from django.contrib.auth.models import User
from coastal.apps.product.models import Product
from coastal.apps.rental.models import RentalOrder
from coastal.apps.message.managers import DialogueManager
from django.db.models.signals import post_save


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


def post_save_dialogue(sender, **kwargs):
    instance = kwargs['instance']
    owner = getattr(instance, 'owner')
    guest = getattr(instance, 'guest')
    product = getattr(instance, 'product')
    dialogue = Dialogue.objects.filter(owner=owner, guest=guest, product=product).first()
    if not dialogue:
        return
    dialogue.order = instance
    dialogue.save()
post_save.connect(post_save_dialogue, sender=RentalOrder, weak=False, dispatch_uid='RentalOrder_post_save_dialogue')
