from __future__ import unicode_literals

from django.db import migrations


def update_category(apps, schema_editor):
    Category = apps.get_model('product', 'Category')
    Category.objects.create(id=9, path='0004', depth=1, numchild=0, name='Experience', full_name='Experience')


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0048_auto_20170206_2226'),
    ]

    operations = [
        migrations.RunPython(update_category),
    ]
