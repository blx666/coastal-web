from django.conf.urls import url

from coastal.api.product import views


urlpatterns = [
    url(r'^filter/', views.product_list, name='product-list'),
    url(r'^(?P<pid>\d+)/', views.product_detail, name='product-detail'),
    url(r'^upload_image/$', views.product_image_upload, name='product-upload-images'),
]
