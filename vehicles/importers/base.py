import logging

from vehicles.models import DataSource

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

    def run(self):
        raise NotImplementedError
