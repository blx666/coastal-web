from django.db import migrations


def update_rentalorder_status(apps, schema_editor):

    RentalOrder = apps.get_model('rental', 'RentalOrder')
    rental_orders = RentalOrder.objects.all()
    status_list = ['booked', 'check-in', 'paid', 'check-out', 'finished']
    for rental_order in rental_orders:
        if rental_order.status in status_list:
            rental_order.date_succeed = rental_order.date_updated
            rental_order.save()


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0017_rentalorder_date_succeed'),
    ]

    operations = [
        migrations.RunPython(update_rentalorder_status),
    ]

