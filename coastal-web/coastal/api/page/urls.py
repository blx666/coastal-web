from django.conf.urls import url

from coastal.api.page import views

urlpatterns = [
    url(r'^home/$', views.home, name='home'),
    url(r'^360-images/$', views.images_360, name='images'),
]
