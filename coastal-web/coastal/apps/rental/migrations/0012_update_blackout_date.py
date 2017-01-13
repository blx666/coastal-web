# -*- coding: utf-8 -*-
import datetime
from django.db import migrations


def update_blackout_date(apps, schema_editor):
    BlackOutDate = apps.get_model('rental', 'BlackOutDate')
    blackout_date = BlackOutDate.objects.all()
    for date in blackout_date:
        date.start_date = date.start_date
        date.end_date = (date.end_date + datetime.timedelta(hours=23, minutes=59, seconds=59))
        date.save()


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0011_auto_20170111_0032'),
    ]

    operations = [
        migrations.RunPython(update_blackout_date),
    ]
