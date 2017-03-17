from django.apps import AppConfig
from django.db.models.signals import post_migrate


def post_migrate_callback(sender, **kwargs):
    from .utils import populate_event_types
    populate_event_types()


class VehiclesConfig(AppConfig):
    name = 'vehicles'

    def ready(self):
        post_migrate.connect(post_migrate_callback, sender=self)

        from vehicles.importers import register_importers_from_settings
        register_importers_from_settings()
