# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-16 02:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0016_auto_20170222_0136'),
    ]

    operations = [
        migrations.AddField(
            model_name='rentalorder',
            name='order_succeed',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
