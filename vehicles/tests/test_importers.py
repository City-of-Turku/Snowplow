from django.test import override_settings

from vehicles.importers import (
    get_importer_by_id, register_importer, register_importers_from_settings
)
from vehicles.importers.base import BaseVehicleImporter


TEST_IMPORTERS = {
    '%s.DummyImporter' % __name__: {
        'URL': 'https://api.dummy.com/v1/',
    },
}


class DummyImporter(BaseVehicleImporter):
    id = 'dummy_importer'

    def run(self):
        pass


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


@override_settings(STREET_MAINTENANCE_IMPORTERS=TEST_IMPORTERS)
def test_automatic_registering():
    from vehicles import importers
    importers._importers = {}
    register_importers_from_settings()

    importer = get_importer_by_id('dummy_importer')
    assert isinstance(importer, DummyImporter)
    assert importer.settings['URL'] == 'https://api.dummy.com/v1/'
