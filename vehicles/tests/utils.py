import json

from django.core.urlresolvers import reverse
from django.utils import timezone
from rest_framework.test import APIClient

VEHICLE_LIST_URL = reverse('v1:vehicle-list')

TWO_YEARS_IN_SECONDS = 60 * 60 * 24 * 365 * 2


def get_detail_url(vehicle):
    return reverse('v1:vehicle-detail', kwargs={'pk': vehicle.id})


def get(url, params=None):
    api_client = APIClient()
    response = api_client.get(url, params)
    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    return json.loads(response.content.decode('utf-8'))


def get_list(params=None):
    return get(VEHICLE_LIST_URL, params)


def get_detail(vehicle, params=None):
    return get(get_detail_url(vehicle), params)


def get_location_data_from_obj(obj):
    return {
        'coords': [obj.coords.x, obj.coords.y],
        'timestamp': timezone.localtime(obj.timestamp).isoformat(),
        'events': [ev.identifier for ev in obj.events.all()],
    }
