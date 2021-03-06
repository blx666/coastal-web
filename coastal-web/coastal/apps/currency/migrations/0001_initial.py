# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-22 05:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=3)),
                ('symbol', models.CharField(max_length=2)),
                ('rate', models.FloatField(help_text='here is the rate base on dollar')),
            ],
            options={
                'verbose_name_plural': 'Currencies',
            },
        ),
    ]
