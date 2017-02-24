from __future__ import unicode_literals

from django.db import migrations


def update_category(apps, schema_editor):
    Category = apps.get_model('product', 'Category')
    Category.objects.filter(id=9, name='Experience', full_name='Experience').update(name='Adventure', full_name='Adventure')


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0049_update_category_experience'),
    ]

    operations = [
        migrations.RunPython(update_category),
    ]
