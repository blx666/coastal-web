# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-12 02:38
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0006_currency_update_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='currency',
            name='update_time',
        ),
        migrations.AddField(
            model_name='currency',
            name='update_rate_time',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 12, 2, 38, 12, 525214, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
