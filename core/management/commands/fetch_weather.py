#!/usr/bin/env python
"""Django management command to fetch weather data for all farms"""
from django.core.management.base import BaseCommand
from core.tasks import fetch_weather_data
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually fetch weather data for all active farms'

    def handle(self, *args, **options):
        self.stdout.write("🌦️  Executing fetch_weather_data...")
        
        try:
            result = fetch_weather_data()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Success: {result}')
            )
        except Exception as e:
            logger.error(f"Weather fetch error: {e}", exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
