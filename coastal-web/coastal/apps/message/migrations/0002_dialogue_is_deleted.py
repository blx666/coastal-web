# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-06 10:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('message', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dialogue',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
