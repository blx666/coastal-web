# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-09 09:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0015_auto_upper_to_lower'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='invite_code',
            field=models.CharField(blank=True, max_length=32),
        ),
    ]