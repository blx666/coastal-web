# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-22 09:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0013_auto_20170110_0822'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='client',
            field=models.CharField(blank=True, choices=[('', '-------'), ('facebook', 'Facebook')], default='', max_length=20),
        ),
    ]
