# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-10 16:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0012_userprofile_stripe_customer_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.CharField(choices=[('in', 'in'), ('out', 'out')], max_length=32),
        ),
    ]
