from django.conf.urls import url
from coastal.api.account import views
from django.contrib.auth import logout

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^register/check-email/$', views.check_email, name='register-check-email'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^update-profile/$', views.update_profile, name='update-profile'),
    url(r'^my-profile/$', views.my_profile, name='my-profile'),
]