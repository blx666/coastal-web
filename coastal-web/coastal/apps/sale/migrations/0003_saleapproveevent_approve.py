# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-14 07:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sale', '0002_add_saleapproveevent_salepaymentevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleapproveevent',
            name='approve',
            field=models.BooleanField(default=1),
            preserve_default=False,
        ),
    ]