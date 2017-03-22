from datetime import datetime
from unittest.mock import Mock

import pytest
from django.conf import ImproperlyConfigured
from django.utils import timezone

from vehicles.importers import (
    get_importer_by_id, register_importer, register_importers_from_settings
)
from vehicles.importers.base import BaseVehicleImporter
from vehicles.importers.kuntoturku import KuntoTurkuImporter
from vehicles.models import DataSource, Vehicle


FETCHED_DATA_1 = [
    {
        'id': 123,
        'machine_type': 'kuorma-auto',
        'last_location': {
            'timestamp': '2017-02-18 12:00:00',
            'coords': '(20.2325767544403 60.3134866561725)',
            'events': ['Auraus', 'Siirtymäajo']
        }
    },
    {
        'id': 456,
        'machine_type': 'kuorma-auto',
        'last_location': {
            'timestamp': '2017-02-18 13:00:00',
            'coords': '(21.2325767544403 61.3134866561725)',
            'events': ['Auraus', 'Siirtymäajo']
        }
    },
]

FETCHED_DATA_2 = [
    # THIS HAS NOT BEEN UPDATED
    {
        'id': 123,
        'machine_type': 'kuorma-auto',
        'last_location': {
            'timestamp': '2017-02-18 12:00:00',
            'coords': '(20.2325767544403 60.3134866561725)',
            'events': ['Auraus', 'Siirtymäajo']
        }
    },
    # THIS HAS BEEN UPDATED
    {
        'id': 456,
        'machine_type': 'kuorma-auto',
        'last_location': {
            'timestamp': '2017-02-18 13:15:00',
            'coords': '(22.2325767544403 62.3134866561725)',
            'events': ['Pesu', 'foo', 'Hiekoitus']
        }
    },

]


class DummyImporter(BaseVehicleImporter):
    id = 'dummy_importer'

    def run(self):
        pass


@pytest.fixture(autouse=True)
def default_settings(settings):
    settings.STREET_MAINTENANCE_DELAY = 15 * 60
    settings.STREET_MAINTENANCE_IMPORTERS = {
        '%s.DummyImporter' % __name__: {
            'URL': 'https://api.dummy.com/v1/',
        },
}


def test_importer_creation():
    dummy_importer = DummyImporter({'dummy_setting': 'dummy_value'})
    assert dummy_importer.settings['dummy_setting'] == 'dummy_value'
    assert round(dummy_importer.run_interval) == 5  # hardcoded default

    dummy_importer_with_interval = DummyImporter({'RUN_INTERVAL': 10.0})
    assert round(dummy_importer_with_interval.run_interval) == 10.0


def test_importer_registering():
    dummy_importer = DummyImporter()
    register_importer(dummy_importer)

    assert get_importer_by_id('dummy_importer') == dummy_importer
    assert get_importer_by_id('damdidam') is None


def test_automatic_registering():
    from vehicles import importers
    importers._importers = {}
    register_importers_from_settings()

    importer = get_importer_by_id('dummy_importer')
    assert isinstance(importer, DummyImporter)
    assert importer.settings['URL'] == 'https://api.dummy.com/v1/'


def test_kunto_turku_importer_url_required():
    with pytest.raises(ImproperlyConfigured):
        # URL missing
        KuntoTurkuImporter({'foo': 'bar'})


def test_kunto_turku_importer_basic_import():
    importer = KuntoTurkuImporter({'URL': 'https://api.dummy.com/v1/'})

    importer.fetch_data = Mock(return_value=FETCHED_DATA_1)
    importer.run()

    assert Vehicle.objects.count() == 2

    vehicle = Vehicle.objects.get(origin_id='123')
    assert vehicle.data_source == DataSource.objects.get(id=KuntoTurkuImporter.id)

    assert vehicle.locations.count() == 1
    location = vehicle.locations.last()

    assert vehicle.last_location == location
    assert location.timestamp == timezone.make_aware(datetime(2017, 2, 18, 12, 00, 00))
    assert round(location.coords.x) == 20
    assert round(location.coords.y) == 60
    assert {event.identifier for event in location.events.all()} == {'au'}


def test_kuntoturku_importer_two_imports():
    importer = KuntoTurkuImporter({'URL': 'https://api.dummy.com/v1/'})

    importer.fetch_data = Mock(return_value=FETCHED_DATA_1)
    importer.run()

    importer.fetch_data = Mock(return_value=FETCHED_DATA_2)
    importer.run()

    assert Vehicle.objects.count() == 2

    # check that the first vehicle has not been updated
    first_vehicle = Vehicle.objects.get(origin_id='123')
    assert first_vehicle.last_location.timestamp == timezone.make_aware(datetime(2017, 2, 18, 12, 00, 00))
    assert first_vehicle.locations.count() == 1

    # check that the second vehicle has been updated
    second_vehicle = Vehicle.objects.get(origin_id='456')
    assert second_vehicle.last_location.timestamp == timezone.make_aware(datetime(2017, 2, 18, 13, 15, 00))
    assert second_vehicle.locations.count() == 2

    # should not be affected
    old_location = second_vehicle.locations.first()
    assert old_location.timestamp == timezone.make_aware(datetime(2017, 2, 18, 13, 00, 00))
    assert {event.identifier for event in old_location.events.all()} == {'au'}

    # should be the new location
    new_location = second_vehicle.locations.last()
    assert new_location.timestamp == timezone.make_aware(datetime(2017, 2, 18, 13, 15, 00))
    assert {event.identifier for event in new_location.events.all()} == {'pe', 'hi'}
