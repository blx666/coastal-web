# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-10 07:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0003_merge_20170117_0315'),
    ]

    operations = [
        migrations.CreateModel(
            name='InviteCodes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invite_code', models.CharField(max_length=32)),
            ],
        ),
    ]
