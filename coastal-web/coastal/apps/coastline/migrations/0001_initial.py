# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-18 09:51
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Coastline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scale_rank', models.FloatField()),
                ('feature', models.CharField(max_length=20)),
                ('m_line_string', django.contrib.gis.db.models.fields.MultiLineStringField(srid=4326)),
            ],
        ),
    ]
