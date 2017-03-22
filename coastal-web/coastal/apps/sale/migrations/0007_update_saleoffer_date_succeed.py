from django.db import migrations


def update_saleoffer_status(apps, schema_editor):

    SaleOffer = apps.get_model('sale', 'SaleOffer')
    sale_offers = SaleOffer.objects.all()
    status_list = ['pay', 'finished']
    for sale_offer in sale_offers:
        if sale_offer.status in status_list:
            sale_offer.date_succeed = sale_offer.date_updated
            sale_offer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('sale', '0006_saleoffer_date_succeed'),
    ]

    operations = [
        migrations.RunPython(update_saleoffer_status),
    ]

