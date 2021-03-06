from django.conf.urls import url

from coastal.api.rental import views


urlpatterns = [
    url(r'^book-rental/$', views.book_rental, name='book-rental'),
    url(r'^approve/$', views.rental_approve, name='rental-approve'),
    url(r'^payment/stripe/$', views.payment_stripe, name='payment-stripe'),
    url(r'^payment/coastal/$', views.payment_coastal, name='payment-coastal'),
    url(r'^detail/$', views.order_detail, name='detail'),
    url(r'^delete-order/$', views.delete_order, name='delete-order'),
]
