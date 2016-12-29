from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils.functional import cached_property
from treebeard.mp_tree import MP_Node

from coastal.apps.product import defines as defs
from coastal.core.storage import ImageStorage


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
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled')
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

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
    max_guests = models.PositiveSmallIntegerField(blank=True, null=True)
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

    currency = models.CharField(max_length=3, default='USD', blank=True)

    # rental info
    rental_price = models.FloatField(help_text='here is the price per day', null=True, blank=True)
    rental_usd_price = models.FloatField('Rental USD Price', null=True, blank=True)
    rental_unit = models.CharField(max_length=32, choices=CHARGE_UNIT_CHOICES, blank=True)
    rental_type = models.CharField(max_length=32, choices=ALLOW_RENTAL_CHOICES, blank=True,
                                   help_text='Who can book instantly')
    rental_rule = models.TextField(blank=True)
    discount_weekly = models.IntegerField(null=True, blank=True, help_text="The unit is %. e.g. 60 means 60%")
    discount_monthly = models.IntegerField(null=True, blank=True, help_text="The unit is %. e.g. 60 means 60%")

    # sale info
    sale_price = models.FloatField(default=0, null=True, blank=True)

    # description
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    amenities = models.ManyToManyField('Amenity')
    desc_about_it = models.TextField(null=True, blank=True)
    desc_guest_access = models.TextField(null=True, blank=True)
    desc_interaction = models.TextField(null=True, blank=True)
    desc_getting_around = models.TextField(null=True, blank=True)
    desc_other_to_note = models.TextField(null=True, blank=True)

    # score
    score = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    @cached_property
    def short_desc(self):
        if self.category_id in (defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT):
            short_desc = 'Entire House/Apartment with %s Rooms hosted by %s' % (self.rooms, self.owner.get_full_name())
        elif self.category_id == defs.CATEGORY_ROOM:
            short_desc = 'Private Room hosted by %s' % self.owner.get_full_name()
        elif self.category_id == defs.CATEGORY_BOAT_SLIP:
            short_desc = '%s ft. Boatslip hosted by %s' % (self.length, self.owner.get_full_name())
        elif self.category_id == defs.CATEGORY_YACHT:
            short_desc = '%s ft. Yacht hosted by %s' % (self.length, self.owner.get_full_name())
        elif self.category_id == defs.CATEGORY_JET:
            short_desc = '%s ft. Aircraft hosted by %s' % (self.length, self.owner.get_full_name())
        else:
            short_desc = '%s ft. %s' % (self.length, self.category.name.lower())
        return short_desc

    def get_amenities_display(self):
        return ', '.join(self.amenities.values_list('name', flat=True))

    def publish(self):
        self.status = 'published'

    def validate_publish_data(self):
        if not (self.for_sale or self.for_rental):
            return False

        if self.for_rental:
            if not (self.rental_price and self.rental_unit and self.rental_type and self.rental_rule and self.currency):
                return False

        if self.for_sale:
            if not self.currency:
                return False

        if self.category_id == defs.CATEGORY_JET:
            if not (self.cabins and self.beds and self.sleeps and self.bathrooms and self.length and self.year):
                return False
        elif self.category_id in (defs.CATEGORY_HOUSE, defs.CATEGORY_APARTMENT):
            if not (self.rooms and self.sleeps and self.beds and self.bathrooms):
                return False
        elif self.category_id == defs.CATEGORY_ROOM:
            if not (self.sleeps and self.beds and self.bathrooms):
                return False
        elif self.category_id == defs.CATEGORY_YACHT:
            if not (self.cabins and self.beds and self.sleeps and self.bathrooms and self.length and self.depth and self.year and self.speed):
                return False
        elif self.category_id == defs.CATEGORY_BOAT_SLIP:
            if not (self.marina and self.basin and self.stall):
                return False

        return True

    def cancel(self):
        self.status = 'cancelled'


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
    CAPTION_360 = '360-view'
    TYPE_CHOICE = (
        ('', '----'),
        ('360-view', '360 View')
    )
    product = models.ForeignKey(Product, null=True, blank=True)
    image = models.ImageField(upload_to='product/%Y/%m', max_length=255, storage=ImageStorage())
    display_order = models.PositiveSmallIntegerField(default=0)
    caption = models.CharField(max_length=32, choices=TYPE_CHOICE, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)


class RentalBlackOutDate(models.Model):
    product = models.ForeignKey(Product)
    start_date = models.DateField()
    end_date = models.DateField()


class ProductViewCount(models.Model):
    product = models.OneToOneField(Product)
    count = models.PositiveIntegerField(default=0)