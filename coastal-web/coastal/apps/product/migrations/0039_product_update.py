# -*- coding: utf-8 -*-
from django.db import migrations


def update_product_status(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    product_list = Product.objects.all()
    for product in product_list:
        if not product.productimage_set.first():
            product.status = 'draft'
            product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0038_auto_20170105_2245'),
    ]

    operations = [
        migrations.RunPython(update_product_status),
    ]
