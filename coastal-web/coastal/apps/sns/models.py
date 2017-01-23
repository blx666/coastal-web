from django.contrib.gis.db import models
from django.contrib.auth.models import User


class Token(models.Model):
    user = models.ForeignKey(User, related_name="tokens")
    uuid = models.TextField()
    token = models.TextField()
    endpoint = models.TextField()
