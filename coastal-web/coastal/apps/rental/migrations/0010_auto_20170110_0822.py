# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-10 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0009_auto_20170105_2215'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentevent',
            name='customer_token',
        ),
        migrations.AddField(
            model_name='paymentevent',
            name='stripe_amount',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='rentalorder',
            name='coastal_dollar',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='paymentevent',
            name='reference',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
