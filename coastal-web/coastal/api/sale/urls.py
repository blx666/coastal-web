from django.conf.urls import url

from coastal.api.sale import views


urlpatterns = [
    url('approve/$', views.approve, name='approve'),
    url('offer/$', views.sale_detail, name='sale-detail'),
]
