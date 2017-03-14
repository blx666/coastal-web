from django.conf.urls import url
from coastal.api.support import views

urlpatterns = [
    url(r'^send-message/$', views.sent_message, name='send-message'),
    url(r'^setting/$', views.setting, name='setting'),
]

