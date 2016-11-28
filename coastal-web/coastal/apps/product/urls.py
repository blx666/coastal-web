from django.conf.urls import include, url
from . import views


urlpatterns = [
    url(r'^filter/', views.product_list, name='product-list'),
    url(r'^(?P<pid>\d+)/', views.product_detail, name='product-detail'),
]
