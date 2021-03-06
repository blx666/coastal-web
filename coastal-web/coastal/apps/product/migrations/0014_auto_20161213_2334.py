# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-14 07:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_auto_20161213_1913'),
    ]

    operations = [
        migrations.AddField(
            model_name='productimage',
            name='caption',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='productimage',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
