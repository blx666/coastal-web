from django.conf.urls import url

from coastal.api.page import views

urlpatterns = [
    url(r'^home/(?P<page>\d+)/$', views.home, name='home'),
    url(r'^360-images/$', views.images, name='images'),
]
