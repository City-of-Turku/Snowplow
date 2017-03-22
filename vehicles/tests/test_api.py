from datetime import datetime, timedelta

import pytest

from django.utils import timezone

from vehicles.models import EventType, Location
from vehicles.factories import LocationFactory, VehicleFactory
from vehicles.tests.utils import get_list, get_detail, get_location_data_from_obj, TWO_YEARS_IN_SECONDS


@pytest.fixture(autouse=True)
def default_settings(settings):
    settings.STREET_MAINTENANCE_DELAY = None


@pytest.fixture
def vehicle():
    return VehicleFactory.create()


@pytest.fixture
def locations_for_vehicle(vehicle):
    LocationFactory.create_batch(10, vehicle=vehicle)


def test_list_and_detail_endpoint(vehicle, locations_for_vehicle):
    last_location = Location.objects.last()
    last_location.events.add(EventType.objects.get(identifier='au'))
    last_location.events.add(EventType.objects.get(identifier='hi'))

    expected_data = {
        'location_history': [],
        'id': vehicle.id,
        'last_location': get_location_data_from_obj(last_location)
    }

    list_data = get_list()
    assert list_data == [expected_data]

    detail_data = get_detail(vehicle)
    assert detail_data == expected_data


def test_location_history(vehicle, locations_for_vehicle):
    data = get_detail(vehicle, {'history': 3})
    assert len(data['location_history']) == 3

    locations = vehicle.locations.order_by('-timestamp')
    history = data['location_history']

    last_obj = locations[0]
    assert history[2] == get_location_data_from_obj(last_obj)

    second_last_obj = locations[1]
    assert history[1] == get_location_data_from_obj(second_last_obj)


def test_cannot_get_location_history_in_list(locations_for_vehicle):
    data = get_list({'history': 3})
    assert data[0]['location_history'] == []


def test_limit():
    vehicles = VehicleFactory.create_batch(3)
    ids = [vehicle.id for vehicle in vehicles]

    # create location timestamps sequentially for the vehicles
    base_datetime = timezone.make_aware(datetime(2000, 2, 18, 10, 00))
    for i, vehicle in enumerate(vehicles):
        LocationFactory.create(vehicle=vehicle, timestamp=base_datetime + timedelta(seconds=10 * i))

    data = get_list({'limit': 2})
    assert {location['id'] for location in data} == {ids[2], ids[1]}  # second last and last

    data = get_list({'limit': 1})
    assert {location['id'] for location in data} == {ids[2]}  # only last


def test_default_limit():
    LocationFactory.create_batch(15)
    data = get_list()
    assert len(data) == 10


def test_since_in_list():
    old_vehicles = VehicleFactory.create_batch(3)

    for vehicle in old_vehicles:
        LocationFactory.create(vehicle=vehicle, year=2000)

    new_vehicles = VehicleFactory.create_batch(3)
    new_ids = [vehicle.id for vehicle in new_vehicles]

    for vehicle in new_vehicles:
        LocationFactory.create(vehicle=vehicle, year=timezone.now().year - 1)

    data = get_list({'since': '2years ago'})
    assert {location['id'] for location in data} == set(new_ids)


def test_since_in_detail(vehicle):
    LocationFactory.create_batch(4, vehicle=vehicle, year=2000)
    LocationFactory.create_batch(7, vehicle=vehicle, year=timezone.now().year - 1)

    data = get_detail(vehicle, {'since': '2years ago'})
    assert len(data['location_history']) == 7


def test_temporal_resolution(vehicle):
    for i in range(10):
        base_datetime = timezone.make_aware(datetime(2000, 2, 18, 10, 00))
        LocationFactory.create(vehicle=vehicle, timestamp=base_datetime + timedelta(seconds=i))

    data = get_detail(vehicle, {'history': 10, 'temporal_resolution': 2})
    assert len(data['location_history']) == 5


def test_delay_in_list(settings):
    settings.STREET_MAINTENANCE_DELAY = TWO_YEARS_IN_SECONDS

    vehicle_from_2000 = VehicleFactory.create()
    LocationFactory.create_batch(4, vehicle=vehicle_from_2000, year=2000)
    vehicle_from_2000.update_last_location()

    vehicle_from_last_year = VehicleFactory.create()
    LocationFactory.create_batch(7, vehicle=vehicle_from_last_year, year=timezone.now().year - 1)
    vehicle_from_last_year.update_last_location()

    data = get_list()
    assert {vehicle['id'] for vehicle in data} == {vehicle_from_2000.id}


def test_delay_in_detail(vehicle, settings):
    settings.STREET_MAINTENANCE_DELAY = TWO_YEARS_IN_SECONDS

    LocationFactory.create_batch(4, vehicle=vehicle, year=2000)
    LocationFactory.create_batch(7, vehicle=vehicle, year=timezone.now().year - 1)
    vehicle.update_last_location()

    data = get_detail(vehicle, {'history': 100})
    assert len(data['location_history']) == 4
