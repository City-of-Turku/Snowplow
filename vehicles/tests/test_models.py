from django.utils import timezone

from vehicles.factories import LocationFactory, VehicleFactory
from vehicles.tests.utils import TWO_YEARS_IN_SECONDS


def test_last_location_without_delay(settings):
    settings.STREET_MAINTENANCE_DELAY = None

    vehicle = VehicleFactory.create()
    location = LocationFactory.create(vehicle=vehicle, year=2000)

    assert vehicle.last_location == location

    # should not affect anything
    vehicle.update_last_location()

    assert vehicle.last_location == location


def test_last_locations_with_delay(settings):
    settings.STREET_MAINTENANCE_DELAY = TWO_YEARS_IN_SECONDS

    vehicle = VehicleFactory.create()
    location_1 = LocationFactory.create(vehicle=vehicle, year=2000)
    location_2 = LocationFactory.create(vehicle=vehicle, year=timezone.now().year - 1)

    assert vehicle.last_location == location_1

    # should not affect anything
    vehicle.update_last_location()

    assert vehicle.last_location == location_1

    # should not affect anything
    LocationFactory.create(vehicle=vehicle, year=1999)
    vehicle.update_last_location()

    assert vehicle.last_location == location_1

    # this should be the new last location
    location_4 = LocationFactory.create(vehicle=vehicle, year=timezone.now().year - 3)
    vehicle.update_last_location()

    assert vehicle.last_location == location_4

    settings.STREET_MAINTENANCE_DELAY = 60

    # should update last location to location 2 because it is outside delay now
    vehicle.update_last_location()

    assert vehicle.last_location == location_2
