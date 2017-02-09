# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-06 10:31
from __future__ import unicode_literals

import math

from django.db import migrations, models
from coastal.apps.currency.utils import get_exchange_rate


def update_sale_usd_price(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    products = Product.objects.all()
    for product in products:
        currency_rate = get_exchange_rate(product.currency)
        product.sale_usd_price = math.ceil(product.sale_price / currency_rate)
        product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0046_update_product_20170118_2233'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sale_usd_price',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='Rental USD Price'),
        ),
        migrations.RunPython(update_sale_usd_price),
    ]