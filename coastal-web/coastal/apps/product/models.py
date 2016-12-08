from django.contrib.gis.db import models
from django.contrib.auth.models import User

from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    """
    A product category. Uses django-treebeard.
    """
    name = models.CharField(max_length=255, db_index=True)
    full_name = models.CharField(max_length=255, db_index=True, editable=False)

    _full_name_separator = ' > '

    def __str__(self):
        return self.full_name

    def update_full_name(self, commit=True):
        """
        Updates the instance's full_name. Use update_children_full_name for updating
        the rest of the tree.
        """
        parent = self.get_parent()
        # If category has a parent, includes the parents slug in this one
        if parent:
            self.full_name = '%s%s%s' % (
                parent.full_name, self._full_name_separator, self.name)
        else:
            self.full_name = self.name
        if commit:
            self.save()

    def update_children_full_name(self):
        for child in self.get_children():
            child.update_full_name()
            child.update_children_full_name()

    def save(self, update_full_name=True, *args, **kwargs):
        if update_full_name:
            self.update_full_name(commit=False)

        # If update_fields is specified and name are listed then update the child categories
        update_fields = kwargs.get('update_fields', None)
        if not update_fields or 'name' in update_fields:
            super(Category, self).save(*args, **kwargs)
            self.update_children_full_name()
        else:
            super(Category, self).save(*args, **kwargs)

    def move(self, target, pos=None):
        """
        Moves the current node and all its descendants to a new position relative to another node.
        """
        super(Category, self).move(target, pos)

        # We need to reload self as 'move' doesn't update the current instance,
        # then we iterate over the subtree and call save which automatically
        # updates slugs.
        reloaded_self = self.__class__.objects.get(pk=self.pk)
        reloaded_self.update_full_name()
        reloaded_self.update_children_full_name()

    def get_ancestors_and_self(self):
        """
        Gets ancestors and includes itself. Use treebeard's get_ancestors
        if you don't want to include the category itself. It's a separate function as it's commonly used in templates.
        """
        return list(self.get_ancestors()) + [self]

    def get_descendants_and_self(self):
        """
        Gets descendants and includes itself. Use treebeard's get_descendants
        if you don't want to include the category itself. It's a separate function as it's commonly used in templates.
        """
        return list(self.get_descendants()) + [self]

    def has_children(self):
        return self.get_num_children() > 0

    def get_num_children(self):
        return self.get_children().count()

    class Meta:
        ordering = ['path']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Product(models.Model):
    CHARGE_UNIT_CHOICES = (
        (1, 'Day'),
        (2, 'Week'),
        (3, 'Month'),
    )

    category = models.ForeignKey(Category)
    owner = models.ForeignKey(User)

    name = models.CharField(max_length=255)
    description = models.TextField()
    amenities = models.TextField()
    max_guests = models.PositiveSmallIntegerField()
    beds = models.PositiveSmallIntegerField()
    bathrooms = models.PositiveSmallIntegerField()
    sleeps = models.PositiveSmallIntegerField()

    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    for_rental = models.BooleanField()
    for_sale = models.BooleanField()

    rental_price = models.FloatField(help_text='here is the price per day')
    # rental_currency = models.ForeignKey()
    rental_usd_price = models.FloatField('Rental USD Price')
    rental_unit = models.PositiveSmallIntegerField(choices=CHARGE_UNIT_CHOICES)
    point = models.PointField()


class Space(Product):
    pass


class Yacht(Product):
    pass


class Jet(Product):
    pass


class ProductImage(models.Model):
    product = models.ForeignKey(Product, null=True)
    image = models.ImageField(upload_to='product/%Y/%m', max_length=255)
    display_order = models.PositiveSmallIntegerField(default=0)
