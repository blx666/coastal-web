from django.conf.urls import url

from coastal.api.sale import views


urlpatterns = [
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^offer/$', views.sale_detail, name='sale-detail'),
    url(r'^make-offer/$', views.make_offer, name='make-offer'),
    url(r'^delete-offer/$', views.delete_offer, name='delete-offer'),
]
