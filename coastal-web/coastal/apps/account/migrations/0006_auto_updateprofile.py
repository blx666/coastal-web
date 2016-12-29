# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-14 11:46
from __future__ import unicode_literals

from django.db import migrations


def update_profile(apps, schema_editor):
    UserProfile = apps.get_model("account", "UserProfile")
    User = apps.get_model("auth", "User")
    user_list = User.objects.all()
    for user in user_list:
        if hasattr(user, 'userprofile'):
            continue
        else:
            UserProfile.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_auto_20161213_2334'),
    ]

    operations = [
        migrations.RunPython(update_profile),
    ]