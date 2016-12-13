# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-12 06:26
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0003_add_productimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, choices=[('common', 'Common'), ('extra', 'Extra')], max_length=32, null=True)),
                ('amenity_type', models.CharField(blank=True, choices=[('common', 'Common'), ('extra', 'Extra')], max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FavouriteProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='jet',
            name='product_ptr',
        ),
        migrations.RemoveField(
            model_name='space',
            name='product_ptr',
        ),
        migrations.RemoveField(
            model_name='yacht',
            name='product_ptr',
        ),
        migrations.AddField(
            model_name='product',
            name='basin',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='cabins',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='depth',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='desc_about_it',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='desc_getting_around',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='desc_guest_access',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='desc_interaction',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='desc_other_to_note',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='marina',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='rental_rule',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='rental_type',
            field=models.PositiveSmallIntegerField(blank=True, choices=[('rental_true', 'direct_rental_true'), ('rental_false', 'direct_rental_false')], help_text='Who can book instantly', null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='rooms',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='sale_price',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='speed',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='stall',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='product',
            name='year',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RemoveField(
            model_name='product',
            name='amenities',
        ),
        migrations.AlterField(
            model_name='product',
            name='bathrooms',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='beds',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='point',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='product',
            name='rental_unit',
            field=models.PositiveSmallIntegerField(blank=True, choices=[('day', 'Day'), ('half-day', 'Half-Day'), ('hour', 'Hour')], null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='rental_usd_price',
            field=models.FloatField(verbose_name='Rental USD Price'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sleeps',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='product.Product'),
        ),
        migrations.DeleteModel(
            name='Jet',
        ),
        migrations.DeleteModel(
            name='Space',
        ),
        migrations.DeleteModel(
            name='Yacht',
        ),
        migrations.AddField(
            model_name='favouriteproduct',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product'),
        ),
        migrations.AddField(
            model_name='favouriteproduct',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='product',
            name='amenities',
            field=models.ManyToManyField(blank=True, null=True, to='product.Amenity'),
        ),
    ]
