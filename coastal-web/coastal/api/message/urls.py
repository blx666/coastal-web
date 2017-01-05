from django.conf.urls import url
from coastal.api.message import views


urlpatterns = [
    url(r'^create-dialogue/$', views.create_dialogue, name='dialogue-create-dialogue'),
    url(r'^list/$', views.dialogue_list, name='dialogue-list'),
]