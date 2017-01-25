# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-06 06:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0008_merge_20170105_2203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rentalorder',
            name='status',
            field=models.CharField(choices=[('request', 'Unconfirmed'), ('approved', 'Approved'), ('declined', 'Declined'), ('invalid', 'Invalid'), ('charge', 'Unpaid'), ('booked', 'In Transaction'), ('check-in', 'In Transaction'), ('paid', 'In Transaction'), ('check-out', 'In Transaction'), ('finished', 'Finished')], max_length=32),
        ),
    ]