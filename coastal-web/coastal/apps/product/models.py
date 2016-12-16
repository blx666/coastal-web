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
        ('day', 'Day'),
        ('half-day', 'Half-Day'),
        ('hour', 'Hour'),
    )
    ALLOW_RENTAL_CHOICES = (
        ('meet-cr', 'Guests who meet Coastal\'s requirements'),
        ('no-one', 'No one. I will read and approve every request within 24 hours'),
    )
    category = models.ForeignKey(Category)
    for_rental = models.BooleanField()
    for_sale = models.BooleanField()
    owner = models.ForeignKey(User, related_name='properties')

    # address info
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    point = models.PointField(blank=True, null=True)

    # basic info
    max_guests = models.PositiveSmallIntegerField()
    beds = models.PositiveSmallIntegerField(blank=True, null=True)
    bathrooms = models.PositiveSmallIntegerField(blank=True, null=True)
    sleeps = models.PositiveSmallIntegerField(blank=True, null=True)
    rooms = models.PositiveSmallIntegerField(blank=True, null=True)
    marina = models.CharField(max_length=255, blank=True)
    basin = models.CharField(max_length=255, blank=True)
    stall = models.CharField(max_length=255, blank=True)
    length = models.PositiveSmallIntegerField(blank=True, null=True)
    depth = models.PositiveSmallIntegerField(blank=True, null=True)
    cabins = models.PositiveSmallIntegerField(blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    speed = models.PositiveSmallIntegerField(blank=True, null=True)

    # rental info
    rental_price = models.FloatField(help_text='here is the price per day')
    # rental_currency = models.ForeignKey()
    rental_usd_price = models.FloatField('Rental USD Price')
    rental_unit = models.CharField(max_length=32, choices=CHARGE_UNIT_CHOICES, null=True, blank=True)
    rental_type = models.CharField(max_length=32, choices=ALLOW_RENTAL_CHOICES, null=True, blank=True,
                                   help_text='Who can book instantly')
    rental_rule = models.TextField(blank=True)
    # sale info
    sale_price = models.FloatField(null=True, blank=True)

    # description
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    amenities = models.ManyToManyField('Amenity', blank=True, null=True)
    desc_about_it = models.TextField(max_length=255, null=True, blank=True)
    desc_guest_access = models.TextField(max_length=255, null=True, blank=True)
    desc_interaction = models.TextField(max_length=255, null=True, blank=True)
    desc_getting_around = models.TextField(max_length=255, null=True, blank=True)
    desc_other_to_note = models.TextField(max_length=255, null=True, blank=True)

    # score
    score = models.PositiveIntegerField(default=0)

    @property
    def short_desc(self):
        return ''


class Amenity(models.Model):
    TYPE_CHOICES = (
        ('common', 'Most common'),
        ('extra', 'Extras'),
        ('special', 'Special')
    )

    name = models.CharField(max_length=32)
    amenity_type = models.CharField(max_length=32, choices=TYPE_CHOICES)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, null=True)
    image = models.ImageField(upload_to='product/%Y/%m', max_length=255)
    display_order = models.PositiveSmallIntegerField(default=0)
    caption = models.CharField(max_length=64, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class ProductViewCount(models.Model):
    product = models.OneToOneField(Product)
    count = models.PositiveIntegerField(default=0)
