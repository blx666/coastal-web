from django.conf.urls import url
from coastal.apps.account import views

urlpatterns = [
    url(r'^confirm-email/$', views.validate_email_confirm, name='confirm-email'),
    url(r'^sign-up/(?P<invite_code>.+)/$', views.sign_up, name='sign-up'),
]
