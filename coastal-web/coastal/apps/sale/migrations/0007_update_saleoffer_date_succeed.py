from django.db import migrations


def update_saleoffer_status(apps, schema_editor):

    SaleOffer = apps.get_model('sale', 'SaleOffer')
    saleOffers = SaleOffer.objects.all()
    status_list = ['charge', 'pay', 'finished']
    for saleOffer in saleOffers:
        if saleOffer.status in status_list:
            saleOffer.date_succeed = saleOffer.date_updated
            saleOffer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sale', '0006_saleoffer_date_succeed'),
    ]

    operations = [
        migrations.RunPython(update_saleoffer_status),
    ]

