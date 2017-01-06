from django.conf.urls import url

from coastal.api.review import views


urlpatterns = [
    url(r'^write-review/$', views.write_review, name='write-review'),
]
