import logging

from django.conf import settings as django_settings

from vehicles.constants import DELAY_SETTING
from vehicles.models import DataSource, Vehicle

logger = logging.getLogger(__name__)


class BaseVehicleImporter:
    id = None

    def __init__(self, settings=None):
        assert self.id is not None, 'id is required.'

        logger.debug('Initializing importer %s' % self.id)
        settings = settings or {}
        self.data_source, _ = DataSource.objects.get_or_create(id=self.id)
        self.run_interval = settings.get('RUN_INTERVAL', 5.0)
        self.settings = settings

    def base_run(self):
        if getattr(django_settings, DELAY_SETTING, True):
            Vehicle.update_last_locations()
        self.run()

    def run(self):
        raise NotImplementedError
