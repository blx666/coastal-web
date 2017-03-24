from django.conf.urls import url

from coastal.api.v2.product import views


urlpatterns = [
    url(r'^$', views.product_list, name='product-list'),
    url(r'^update/$', views.product_update, name='product-update'),
    url(r'^add/$', views.product_add, name='product-add'),
    url(r'^search/$', views.product_search, name='product-search'),
    url(r'^(?P<pid>\d+)/$', views.product_detail, name='product-detail'),

]
