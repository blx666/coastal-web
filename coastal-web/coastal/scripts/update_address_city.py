import urllib.request
import urllib.parse
import json

from coastal.apps.product.models import Product


key = 'AIzaSyAYvvJ4thuPanNDqOKKaEgKOBP2Ut3CyeY'
result_type = 'locality'


def update_products_address():
    products = Product.objects.order_by('-id')
    for p in products:
        _update_address(p)


def _update_address(product):
    if product.point:
        params = urllib.parse.urlencode({'latlng': '%s,%s' % (product.point.y, product.point.x)})
        url = "https://maps.googleapis.com/maps/api/geocode/json?result_type=%s&%s&key=%s" % (result_type, params, key)
        with urllib.request.urlopen(url) as f:
            data = json.loads(f.read().decode('utf-8'))
            if data.get('status') != 'OK':
                print('status was not OK: %s (%s)' % (product.name, product.id))
                return

            try:
                address_info = {}
                for address in data.get('results', []):
                    address_info['formatted_address'] = address.get('formatted_address', [])

            except:
                print('meet error: %s (%s)' % product.name, product.id)
                return
            product.city_address = address_info['formatted_address']
            print(address_info)
            print('updated: %s' % product.id)
            product.save()
