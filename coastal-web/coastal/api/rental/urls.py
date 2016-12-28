from django.conf.urls import url

from coastal.api.rental import views


urlpatterns = [
    url(r'^book-rental/$', views.book_rental, name='book-rental'),
    url(r'^(?P<rental_order_id>\d+)/approve/$', views.rental_approve, name='rental-approve'),
]
