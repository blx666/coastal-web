# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-13 12:04
from __future__ import unicode_literals

from django.db import migrations


def update_amenities(apps, schema_editor):
    Amenity = apps.get_model("product", "Amenity")

    amenities = (
        (1, 'Essentials', 'common'),
        (2, 'Shampoo', 'common'),
        (3, 'TV', 'common'),
        (4, 'Air conditioning', 'common'),
        (5, 'Heating', 'common'),
        (6, 'Kitchen', 'common'),
        (7, 'Internet', 'common'),
        (8, 'Wifi', 'common'),
        (9, 'Hot tub', 'extra'),
        (10, 'Washer', 'extra'),
        (11, 'Pool', 'extra'),
        (12, 'Dryer', 'extra'),
        (13, 'Breakfast', 'extra'),
        (14, 'Pier parking', 'extra'),
        (15, 'Gym', 'extra'),
        (16, 'Elevator', 'extra'),
        (17, 'Fireplace', 'extra'),
        (18, 'Smoke detector', 'extra'),
        (19, 'Carbon monoxide detector', 'extra'),
        (20, 'First aid kit', 'extra'),
        (21, 'Safety card', 'extra'),
        (22, 'Fire extinguisher', 'extra'),
        (23, '24 hour check-in', 'extra'),
        (24, 'Hair dryer', 'extra'),
        (25, 'Iron', 'extra'),
        (26, 'Desk/workspace', 'extra'),
        (27, 'Family friendly', 'special'),
        (28, 'Smoking allowed', 'special'),
        (29, 'Suitable for events', 'special'),
        (30, 'Pets allowed', 'special'),
        (31, 'Wheelchair accessible', 'special'),
        (32, 'Has pets', 'special'),
    )

    for aid, name, amenity_type in amenities:
        Amenity.objects.create(id=aid, name=name, amenity_type=amenity_type)


def reverse_update_amenities(apps, schema_editor):
    Amenity = apps.get_model("product", "Amenity")

    Amenity.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_merge_20161213_2216'),
    ]

    operations = [
        migrations.RunPython(update_amenities, reverse_update_amenities),
    ]
