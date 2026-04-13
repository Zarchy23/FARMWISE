# core/apps.py

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        # Import signals to register them
        import core.signals
        
        # Attempt to populate weather data on app startup for Render
        self._populate_weather_on_startup()
    
    def _populate_weather_on_startup(self):
        """
        Populate weather data on app startup.
        Ensures Render deployments have weather available immediately.
        """
        try:
            # Only run if not using Django test runner
            import sys
            if 'test' in sys.argv or 'pytest' in sys.argv[0]:
                return
            
            from django.db import connection
            from core.models import Farm, WeatherData
            
            # Check if database is ready
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Check if there are active farms without weather data
            active_farms = Farm.objects.filter(status='active')
            if not active_farms.exists():
                return
            
            farms_needing_weather = 0
            for farm in active_farms:
                if farm.latitude and farm.longitude:
                    weather_data = WeatherData.objects.filter(farm=farm).first()
                    if not weather_data or not weather_data.temperature:
                        farms_needing_weather += 1
            
            if farms_needing_weather > 0:
                logger.info(f"[WEATHER] App startup: {farms_needing_weather} farms need weather data")
                
                # Try to fetch weather data asynchronously
                try:
                    from core.tasks import fetch_weather_data
                    # Run synchronously during startup
                    result = fetch_weather_data()
                    logger.info(f"[WEATHER] App startup populated weather: {result}")
                except Exception as e:
                    logger.warning(f"[WEATHER] App startup fetch failed (will retry on schedule): {e}")
        
        except Exception as e:
            logger.debug(f"[WEATHER] App startup check skipped: {e}")