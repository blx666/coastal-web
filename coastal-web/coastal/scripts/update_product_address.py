import urllib.request
import urllib.parse
import json

from coastal.apps.coastline.utils import distance_from_coastline
from coastal.apps.product.models import Product


ADDRESS_FIELDS = (
    'country',
    'administrative_area_level_1',
    'administrative_area_level_2',
    'locality',
    'sublocality'
)


def update_products_address():
    products = Product.objects.order_by('id')
    for p in products:
        _update_address(p)


def _update_address(product):
    if product.point:
        import time; time.sleep(1)
        params = urllib.parse.urlencode({'latlng': '%s,%s' % (product.point.y, product.point.x)})
        url = "https://maps.googleapis.com/maps/api/geocode/json?%s" % params
        with urllib.request.urlopen(url) as f:
            data = json.loads(f.read().decode('utf-8'))
            if data.get('status') != 'OK':
                print('status was not OK: %s (%s)' % (product.name, product.id))
                return

            try:
                address_info = {}
                for address in data.get('results', []):
                    address_components = address.get('address_components', [])
                    for a in address_components:
                        for k in a['types']:
                            address_info[k] = a['long_name']
            except:
                print('meet error: %s (%s)' % product.name, product.id)
                return

            for field in ADDRESS_FIELDS:
                setattr(product, field, address_info.get(field, ''))

            print('updated: %s' % product.id)
            product.save()


def update_distance_from_coastline():
    products = Product.objects.filter(distance_from_coastal=0.000310713098007635).order_by('id')
    for p in products:
        p.distance_from_coastal = distance_from_coastline(p.point.x, p.point.y) or float('inf')
        p.save()
        print('update #%s to %s' % (p.id, p.distance_from_coastal))
        import time; time.sleep(1)
