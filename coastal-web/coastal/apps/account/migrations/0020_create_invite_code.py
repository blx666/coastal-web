from __future__ import unicode_literals

from django.db import migrations, models
import random
import string


def add_invite_codes(apps, schema_editor):

    InviteCode = apps.get_model('account', 'InviteCode')
    count = 0
    source = list(string.ascii_uppercase)
    source.extend('0123456789')
    while count < 1000000:
        key = ''
        for index in range(11):
            key += random.choice(source)
        _, created = InviteCode.objects.get_or_create(invite_code=key)
        if created:
            count += 1


def reverse_add_invite_codes(apps, schema_editor):
    InviteCode = apps.get_model('account', 'InviteCode')
    InviteCode.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('account', '0019_invite_code_20170213_0201'),
    ]

    operations = [
        migrations.RunPython(add_invite_codes, reverse_add_invite_codes),
    ]
