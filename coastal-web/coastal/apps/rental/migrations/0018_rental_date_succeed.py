from django.db import migrations


def update_rentalorder_status(apps, schema_editor):

    RentalOrder = apps.get_model('rental', 'RentalOrder')
    rentalorders = RentalOrder.objects.all()
    status_list = ['booked', 'check-in', 'paid', 'check-out', 'finished']
    for rentalorder in rentalorders:
        if rentalorder.status in status_list:
            rentalorder.date_succeed = rentalorder.date_updated
            rentalorder.save()


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0017_rentalorder_date_succeed'),
    ]

    operations = [
        migrations.RunPython(update_rentalorder_status),
    ]

