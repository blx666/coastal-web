# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-07 06:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0047_add_sale_usd_price'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['display_order', '-date_created']},
        ),
        migrations.AddField(
            model_name='product',
            name='exp_end_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='exp_start_time',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='exp_time_length',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='exp_time_unit',
            field=models.CharField(blank=True, choices=[('day', 'Day'), ('week', 'Week'), ('hour', 'Hour')], max_length=32),
        ),
        migrations.AlterField(
            model_name='product',
            name='sale_usd_price',
            field=models.FloatField(blank=True, default=0, null=True, verbose_name='Sale USD Price'),
        ),
    ]
