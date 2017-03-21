# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-16 02:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0054_product_city_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='active_product',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='rental_type',
            field=models.CharField(blank=True, choices=[('meet-cr', "Guests who meet Coastal's requirements"), ('no-one', 'No one. I will read and approve every request within 72 hours')], help_text='Who can book instantly', max_length=32),
        ),
    ]
