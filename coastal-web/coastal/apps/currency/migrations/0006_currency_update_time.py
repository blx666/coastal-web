# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-11 08:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0005_update_currency_display'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='update_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
