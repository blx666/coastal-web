from __future__ import unicode_literals

from django.db import migrations


def update_category(apps, schema_editor):
    Product = apps.get_model('product', 'Product')
    Product.objects.filter(category_id=9).update(for_rental=True, for_sale=True)


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0050_update_category_experience_to_adventure'),
    ]

    operations = [
        migrations.RunPython(update_category),
    ]
