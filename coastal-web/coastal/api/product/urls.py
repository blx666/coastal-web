from django.conf.urls import url

from coastal.api.product import views


urlpatterns = [
    url(r'^$', views.product_list, name='product-list'),
    url(r'^(?P<pid>\d+)/$', views.product_detail, name='product-detail'),
    url(r'^update/$', views.product_update, name='product-update'),
    url(r'^upload-image/$', views.product_image_upload, name='product-image-upload'),
    url(r'^add/$', views.product_add, name='product-add'),
    url(r'^calc-total-price/$', views.calc_total_price, name='calc-total-price'),
    url(r'^amenities/$', views.amenity_list, name='amenity-list'),
    url(r'^(?P<pid>\d+)/like-toggle/$', views.toggle_favorite, name='product-like-toggle'),
    url(r'^currency-list/$', views.currency_list, name='currency-list'),
    url(r'^recommended/$', views.recommend_product_list, name='recommend-product-list'),
    url(r'^discount-calculator/$', views.discount_calculator, name='discount-calculator'),
    url(r'^delete-image/$', views.delete_image, name='delete-image'),
    url(r'^black-dates-for-rental/$', views.black_dates_for_rental, name='black-dates-for-rental'),
    url(r'^search/$', views.search, name='search'),
]
