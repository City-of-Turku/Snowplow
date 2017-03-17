from .celery import app as celery_app


default_app_config = 'streetmaintenance.apps.StreetmaintenanceAppConfig'

__all__ = ['celery_app']
