# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-04 13:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_init_coastal_bucket'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coastalbucket',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]