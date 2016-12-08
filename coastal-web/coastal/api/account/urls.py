from django.conf.urls import url

from coastal.api.account import views

urlpatterns = [
    url(r'^register/$', views.register, name='register'),
    url(r'^register/check-email/$', views.check_email, name='register-check-email'),
    url(r'^login/$', views.login, name='login'),
    url(r'^update-profile/$', views.update_profile, name='update-profile'),
]