# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-11 07:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0039_product_update'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rentalblackoutdate',
            name='product',
        ),
        migrations.DeleteModel(
            name='RentalBlackOutDate',
        ),
    ]