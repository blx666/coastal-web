# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-03 09:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0032_auto_20161225_2116'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='timezone',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
