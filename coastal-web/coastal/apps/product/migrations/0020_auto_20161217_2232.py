# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-18 06:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0019_merge_20161216_0116'),
    ]

    operations = [
        migrations.CreateModel(
            name='RentalBlackOutDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('cancelled', 'Cancelled')], default='draft', max_length=20),
        ),
        migrations.AddField(
            model_name='rentalblackoutdate',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product'),
        ),
    ]
