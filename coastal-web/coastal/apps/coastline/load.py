import os
from django.contrib.gis.utils import LayerMapping
from .models import Coastline

coastline_mapping = {
    'scale_rank': 'scalerank',
    'feature': 'featurecla',
    'm_line_string': 'multilinestring',
}

shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'data', 'ne_10m_coastline.shp'),
)


def run(verbose=True):
    lm = LayerMapping(
        Coastline, shp, coastline_mapping,
        transform=False, encoding='iso-8859-1',
    )
    lm.save(strict=True, verbose=verbose)
