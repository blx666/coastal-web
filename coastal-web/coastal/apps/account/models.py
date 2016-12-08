from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    is_agent = models.NullBooleanField()
    agency_email = models.EmailField(max_length=128, null=True)
    agency_name = models.CharField(max_length=128, null=True)
    agency_address = models.CharField(max_length=256, null=True)

    @property
    def has_agency_info(self):
        return self.is_agent is not None
