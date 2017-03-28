from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('vehicles.urls', namespace='v1')),
]
