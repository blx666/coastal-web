# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-08 07:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0053_auto_20170301_2256'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='city_address',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
