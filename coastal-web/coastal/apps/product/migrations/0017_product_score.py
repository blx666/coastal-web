# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-15 06:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0016_auto_20161214_0058'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='score',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]