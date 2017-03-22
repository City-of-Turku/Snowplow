from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from .api import VehicleViewSet


# allow urls without trailing slashes
class SlashlessRouter(DefaultRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = '/?'


router = SlashlessRouter()
router.register('vehicles', VehicleViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
]
