# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-05 14:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_auto_20170104_0533'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='stripe_customer_id',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]