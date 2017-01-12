from django.contrib import admin
from .models import Category, Product, ProductImage, ProductViewCount


class ProductAdmin(admin.ModelAdmin):

    list_display = ['name', 'status', 'score', 'reported']

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            kwargs['fields'] = ['status', 'rank']
        return super(ProductAdmin, self).get_form(request, obj, **kwargs)


admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(Category)
admin.site.register(ProductViewCount)
