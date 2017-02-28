"""coastal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    url(r'^account/', include('coastal.apps.account.urls', namespace='account')),

    url(r'^api/products/', include('coastal.api.product.urls', namespace='product')),
    url(r'^api/account/', include('coastal.api.account.urls', namespace='api-account')),
    url(r'^api/page/', include('coastal.api.page.urls', namespace='page')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/message/', include('coastal.api.message.urls', namespace='message')),
    url(r'^api/rental/', include('coastal.api.rental.urls', namespace='rental')),
    url(r'^api/payment/', include('coastal.api.payment.urls', namespace='payment')),
    url(r'^api/review/', include('coastal.api.review.urls', namespace='review')),
    url(r'^api/sale/', include('coastal.api.sale.urls', namespace='sale')),
    url(r'^api/help-center/', include('coastal.api.support.urls', namespace='help')),

    url(r'^api/v2/products/', include('coastal.api.v2.product.urls', namespace='product-v2')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
