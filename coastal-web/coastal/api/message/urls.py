from django.conf.urls import url
from coastal.api.message import views


urlpatterns = [
    url(r'^create-dialogue/$', views.create_dialogue, name='dialogue-create-dialogue'),
    url(r'^list/$', views.dialogue_list, name='dialogue-list'),
    url(r'^view/(?P<dial_id>\d+)/$', views.dialogue_detail, name='dialogue-detail'),
    url(r'^send-message/$', views.send_message, name='send-message'),
    url(r'^instant_message/(?P<dial_id>\d+)/(?P<mess_id>\d+)/$', views.instant_message, name='instant-message'),
]