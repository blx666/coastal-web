from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from .models import Coastline


def distance_from_coastline(lon, lat):
    """
    Calculate the distance from coastline. If the distance is greater then 100 mile, we will return None.

    :param lon: float
    :param lat: float
    :return: float (unit is mile)
    """
    point = Point(lon, lat, srid=4326)
    coastlines = Coastline.objects.filter(m_line_string__distance_lte=(point, D(mi=100))).annotate(
        distance=Distance('m_line_string', point))
    distance_list = [c.distance.mi for c in coastlines]
    if distance_list:
        return min(distance_list)
