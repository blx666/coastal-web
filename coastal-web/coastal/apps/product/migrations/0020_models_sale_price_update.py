# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-20 02:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0019_merge_20161216_0116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sale_price',
            field=models.FloatField(blank=True, default=0),
        ),
    ]
