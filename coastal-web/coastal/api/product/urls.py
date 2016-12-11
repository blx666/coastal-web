from django.conf.urls import url

from coastal.api.product import views


urlpatterns = [
    url(r'^filter/', views.product_list, name='product-list'),
    url(r'^(?P<pid>\d+)/', views.product_detail, name='product-detail'),
    url(r'^upload-image/$', views.product_image_upload, name='product-image-upload'),
    url(r'^add/$', views.product_add, name='product-add')
]
