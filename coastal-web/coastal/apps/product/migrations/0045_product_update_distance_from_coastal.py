from django.db import migrations
from coastal.apps.coastline.utils import distance_from_coastline


def update_product_distance_from_coastal(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    products = Product.objects.all()
    for product in products:
        if product.point:
            product.distance_from_coastal = distance_from_coastline(product.point[0], product.point[1]) or 99999999
        product.save()


def reserver_update_product_distance_from_coastal(apps, schem_editor):
    Product = apps.get_model('product', 'Product')
    products = Product.objects.all()
    for product in products:
        if product.point:
            product.distance_from_coastal = 0
        product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0044_product_add_distance_from_coastal'),
    ]

    operations = [
        migrations.RunPython(update_product_distance_from_coastal, reserver_update_product_distance_from_coastal),
    ]
