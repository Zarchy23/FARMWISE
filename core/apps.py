# core/apps.py

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Import signals to register them.
        # NOTE: Do NOT run database queries or network calls here. ready() executes
        # for every management command (migrate, collectstatic, shell, etc.) and for
        # each worker process. Weather population is handled by the Celery Beat
        # schedule ('fetch-weather-data') instead.
        import core.signals