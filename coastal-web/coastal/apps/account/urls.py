from django.conf.urls import url
from coastal.apps.account import views

urlpatterns = [
    url(r'^confirm-email/$', views.validate_email_confirm, name='confirm-email'),
    url(r'^sign-up/(?P<invite_code>.+)/$', views.sign_up, name='sign-up'),

    url(r'^password_reset/done/$', views.password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', views.password_reset_complete, name='password_reset_complete'),
]
