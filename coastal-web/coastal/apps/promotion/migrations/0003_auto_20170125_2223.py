# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-26 06:23
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0002_auto_20161222_0006'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homebanner',
            name='point',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
