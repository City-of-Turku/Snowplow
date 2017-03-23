import logging
import os

from celery import Celery

from vehicles.importers import get_importer_by_id, get_importers

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'streetmaintenance.settings')

app = Celery('streetmaintenance')
app.config_from_object('django.conf:settings', namespace='CELERY')

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def run_importer(importer_id):
    importer = get_importer_by_id(importer_id)
    logger.info('Running importer %s' % importer_id)
    importer.base_run()
    logger.info('Import completed successfully')


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    for importer in get_importers():
        logger.debug('Adding periodic task, importer %s, run interval %s' % (importer.id, importer.run_interval))
        sender.add_periodic_task(
            importer.run_interval,
            run_importer.s(importer.id),
            name='import_%s' % importer.id,
            expires=5,
        )
