from django.conf.urls import url, include

urlpatterns = [
    url(r'^products/gsc/', include('sm.product.gsc.urls', namespace='gsc')),
]
