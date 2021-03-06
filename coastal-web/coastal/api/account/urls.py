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
    url(r'^my-activity/$', views.my_activity, name='my-activity'),
    url(r'^my-account/$', views.my_account, name='my-account'),
    url(r'^my-calendar/$', views.my_calendar, name='my-calendar'),
    url(r'^my-calendar/dates/$', views.my_order_dates, name='my-order-dates'),
    url(r'^my-calendar/orders/$', views.my_orders, name='my-orders'),

    url(r'^stripe-info/$', views.stripe_info, name='stripe-info'),
    url(r'^login/facebook/$', views.facebook_login, name='facebook-login'),
    url(r'^invite-code/$', views.invite_codes, name='invite-code'),
    url(r'^password-reset/$', views.password_reset, name='password_reset'),
]
