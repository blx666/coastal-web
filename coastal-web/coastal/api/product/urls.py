from django.conf.urls import url

from coastal.api.product import views


urlpatterns = [
    url(r'^$', views.product_list, name='product-list'),
    url(r'^(?P<pid>\d+)/$', views.product_detail, name='product-detail'),
    url(r'^upload-image/$', views.product_image_upload, name='product-image-upload'),
    url(r'^add/$', views.product_add, name='product-add'),
    # url(r'^home_page/$', views.home_page, name='home-page'),
    url(r'^rental/(?P<pid>\d+)/$', views.get_rental_amount, name='rental-amount'),
]
