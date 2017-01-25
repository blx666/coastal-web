# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def update_currency(apps, schema_editor):
    Currency = apps.get_model('currency', 'Currency')
    currency = (
        ('USD', 'US$'),
        ('NZD', 'NZ$'),
        ('AUD', 'A$'),
        ('HKD', 'HK$'),
        ('CAD', 'CA$'),
        ('JPY', 'JP￥'),
        ('SGD', 'S$'),
        ('CHF', 'CHF'),
        ('EUR', '€'),
        ('GBP', '￡'),
        ('CNY', 'CN¥')
    )

    for code, display in currency:
        Currency.objects.filter(code=code).update(display=display)


def reverse_update_currency(apps, schema_editor):
    Currency = apps.get_model("currency", "Currency")
    Currency.objects.all().update(display='')


class Migration(migrations.Migration):
    dependencies = [
        ('currency', '0004_currency_display'),
    ]

    operations = [
        migrations.RunPython(update_currency, reverse_update_currency),
    ]
