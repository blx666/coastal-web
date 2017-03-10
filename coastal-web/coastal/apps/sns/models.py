from django.contrib.gis.db import models
from django.contrib.auth.models import User


class Token(models.Model):
    user = models.ForeignKey(User, related_name="tokens")
    uuid = models.TextField()
    token = models.TextField()
    endpoint = models.TextField()


class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications')
    message = models.TextField()
    pushed = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)
    extra_attr = models.TextField()
