# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-22 12:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0025_merge_20161221_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount_monthly',
            field=models.IntegerField(blank=True, help_text='The unit is %. e.g. 60 means 60%', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='discount_weekly',
            field=models.IntegerField(blank=True, help_text='The unit is %. e.g. 60 means 60%', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='rental_currency',
            field=models.CharField(default='USD', max_length=3),
        ),
    ]