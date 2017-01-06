from django.conf.urls import url
from coastal.api.message import views


urlpatterns = [
    url(r'^create-dialogue/$', views.create_dialogue, name='dialogue-create-dialogue'),
    url(r'^list/$', views.dialogue_list, name='dialogue-list'),
    url(r'^view/$', views.dialogue_detail, name='dialogue-detail'),
    url(r'^send-message/$', views.send_message, name='send-message'),
    url(r'^get_new_message/$', views.get_new_message, name='get-new-message'),
]