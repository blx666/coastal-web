# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-16 03:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0016_auto_20161214_0058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='caption',
            field=models.CharField(blank=True, choices=[('', '----'), ('360 views', '360 views')], max_length=32, null=True),
        ),
    ]