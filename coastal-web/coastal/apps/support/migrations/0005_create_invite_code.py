from __future__ import unicode_literals

from django.db import migrations, models
import random
import string


def add_invite_codes(apps, schema_editor):

    InviteCodes = apps.get_model('support', 'InviteCodes')
    result = []
    source = list(string.ascii_uppercase)
    source.extend('0123456789')
    while len(result) < 1000000:
        key = ''
        for index in range(11):
            key += random.choice(source)
        if key in result:
            pass
        else:
            result.append(key)
            InviteCodes.objects.create(invite_code=key)


def reverse_add_invite_codes(apps, schema_editor):
    InviteCodes = apps.get_model('support', 'InviteCodes')
    InviteCodes.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('support', '0004_invitecodes'),
    ]

    operations = [
        migrations.RunPython(add_invite_codes, reverse_add_invite_codes),
    ]
