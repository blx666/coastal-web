# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-04 13:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0005_rentalorder_rental_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentalorder',
            name='currency_rate',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='rentalorder',
            name='total_price_usd',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
    ]
