import logging
from importlib import import_module

from django.conf import settings

logger = logging.getLogger(__name__)

_importers = {}


def register_importer(importer):
    from .base import BaseVehicleImporter
    assert isinstance(importer, BaseVehicleImporter), 'Importers must inherit from BaseVehicleImporter.'
    assert importer.id not in _importers, 'Importer with id "%s" already registered.' % importer.id
    _importers[importer.id] = importer


def get_importers():
    return list(_importers.values())


def get_importer_by_id(importer_id):
    return _importers.get(importer_id)


def register_importers_from_settings():
    """
    Import, instantiate and register importers based on importer settings.
    """
    importer_data = getattr(settings, 'STREET_MAINTENANCE_IMPORTERS', {})

    for full_class_name, importer_datum in importer_data.items():
        module_name, class_name = full_class_name.rsplit('.', 1)
        importer_class = getattr(import_module(module_name), class_name)
        importer = importer_class(importer_datum)
        register_importer(importer)
