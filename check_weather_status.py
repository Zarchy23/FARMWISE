#!/usr/bin/env python
"""Check weather data status and manually trigger fetch if needed"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Farm, WeatherData
from core.tasks import fetch_weather_data
import logging

logger = logging.getLogger(__name__)

print("=" * 60)
print("WEATHER DATA STATUS CHECK")
print("=" * 60)

# Check farms
farms = Farm.objects.filter(status='active')
print(f"\n📍 Active farms: {farms.count()}")
for farm in farms[:3]:
    print(f"   - {farm.name}: ({farm.latitude}, {farm.longitude})")

# Check WeatherData
weather_data = WeatherData.objects.all()
print(f"\n🌦️  WeatherData records: {weather_data.count()}")
for wd in weather_data[:3]:
    print(f"   - {wd.farm.name}:")
    print(f"     Temperature: {wd.temperature}°C")
    print(f"     Condition: {wd.condition}")
    print(f"     Humidity: {wd.humidity}%")
    print(f"     Last updated: {wd.last_updated}")
    if wd.forecast_data.get('forecast'):
        print(f"     Forecast items: {len(wd.forecast_data['forecast'])}")

# If no weather data, manually trigger the task
if not weather_data.exists():
    print("\n⚠️  No weather data found. Triggering fetch_weather_data task...")
    try:
        result = fetch_weather_data()
        print(f"✅ Task result: {result}")
        
        # Check if data was created
        weather_data_after = WeatherData.objects.all()
        print(f"\n📊 After fetch: {weather_data_after.count()} WeatherData records")
        for wd in weather_data_after[:3]:
            print(f"   - {wd.farm.name}: {wd.temperature}°C, {wd.condition}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n✅ Weather data exists in database")
    
    # Check if any records have actual data
    empty_records = WeatherData.objects.filter(temperature__isnull=True)
    if empty_records.exists():
        print(f"⚠️  {empty_records.count()} records are empty (NULL temperature)")
        print("\n🔄 Triggering fetch_weather_data task to populate...")
        try:
            result = fetch_weather_data()
            print(f"✅ Task result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("✅ All records have data")
