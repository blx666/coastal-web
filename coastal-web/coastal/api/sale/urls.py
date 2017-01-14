from django.conf.urls import url

from coastal.api.sale import views


urlpatterns = [
    url(r'^approve/$', views.approve, name='approve'),
    url(r'^offer/$', views.sale_detail, name='sale-detail'),
]
