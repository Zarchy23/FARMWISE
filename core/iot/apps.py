# core/iot/apps.py

from django.apps import AppConfig


class IotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.iot'
    verbose_name = 'IoT Device Management'
