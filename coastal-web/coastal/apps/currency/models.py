from django.contrib.gis.db import models


class Currency(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3)
    symbol = models.CharField(max_length=2)
    rate = models.FloatField(help_text='here is the rate base on dollar')

    def __str__(self):
        return self.code

    class Meta:
        verbose_name_plural = "Currencies"
