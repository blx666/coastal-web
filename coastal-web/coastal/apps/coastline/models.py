from django.contrib.gis.db import models


class Coastline(models.Model):
    scale_rank = models.FloatField()
    feature = models.CharField(max_length=20)
    m_line_string = models.MultiLineStringField()
