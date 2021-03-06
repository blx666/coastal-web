# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-23 09:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0029_rename_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='currency',
            field=models.CharField(blank=True, default='USD', max_length=3),
        ),
        migrations.AlterField(
            model_name='product',
            name='rental_type',
            field=models.CharField(blank=True, choices=[('meet-cr', "Guests who meet Coastal's requirements"), (
            'no-one', 'No one. I will read and approve every request within 24 hours')], default='',
                                   help_text='Who can book instantly', max_length=32),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='product',
            name='rental_unit',
            field=models.CharField(blank=True, default='day', choices=[('day', 'Day'), ('half-day', 'Half-Day'), ('hour', 'Hour')],
                                   max_length=32),
        ),
        migrations.AlterField(
            model_name='product',
            name='sale_price',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]
