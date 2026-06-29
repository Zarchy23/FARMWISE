# core/apps.py

from django.apps import AppConfig
import logging
import os

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
        
        # Initialize ML models directory
        self._initialize_ml_models()
    
    def _initialize_ml_models(self):
        """Ensure ML models directory exists"""
        from django.conf import settings
        ml_models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        if not os.path.exists(ml_models_dir):
            os.makedirs(ml_models_dir)
            logger.info(f"Created ML models directory: {ml_models_dir}")
