from django.conf.urls import url
from coastal.api.payment import views

urlpatterns = [
    url(r'^stripe/add-card/$', views.stripe_add_card, name='stripe-add-card'),
]
