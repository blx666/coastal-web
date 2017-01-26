from django.contrib.gis.db import models


class HomeBanner(models.Model):
    image = models.ImageField(upload_to='home_banner')
    city_name = models.CharField(max_length=64)
    display_order = models.PositiveSmallIntegerField(default=0)
    point = models.PointField(null=True, blank=True)

    def __str__(self):
        return self.city_name

    class Meta:
        ordering = ['display_order']
