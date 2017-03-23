from django.db import migrations


def update_invite_record(apps, schema_editor):

    InviteRecord = apps.get_model('account', 'InviteRecord')
    invite_records = InviteRecord.objects.all()
    for invite_record in invite_records:
        invite_record.user_reward = True
        invite_record.referrer_reward = True
        invite_record.save()


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0026_auto_20170323_0242'),
    ]

    operations = [
        migrations.RunPython(update_invite_record),
    ]

