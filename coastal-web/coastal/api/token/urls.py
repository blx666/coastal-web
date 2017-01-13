from django.conf.urls import url
from coastal.api.token import views


urlpatterns = [
    url(r'^bind_token/$', views.bind_token, name='bind_token'),
]
