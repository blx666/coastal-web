# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-21 07:50
from __future__ import unicode_literals

import coastal.core.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0022_merge_20161219_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.ImageField(max_length=255, storage=coastal.core.storage.ImageStorage(), upload_to='product/%Y/%m'),
        ),
    ]
