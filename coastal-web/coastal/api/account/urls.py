from django.conf.urls import url
from coastal.api.account import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^register/check-email/$', views.check_email, name='register-check-email'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^update-profile/$', views.update_profile, name='update-profile'),
    url(r'^my-profile/$', views.my_profile, name='my-profile'),
    url(r'^validate-email/$', views.validate_email, name='validate-email'),
    url(r'^validate-email/confirm/$', views.validate_email_confirm, name=' validate-email-confirm'),
    url(r'^my-activity/$', views.my_activity, name='my-activity'),
    url(r'^my-account/$', views.my_account, name='my-account'),
]
