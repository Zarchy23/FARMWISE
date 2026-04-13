#!/usr/bin/env python
"""Test weather forecast view data structure"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Farm, WeatherData

# Get the farm user
farm = Farm.objects.filter(status='active').first()
if not farm:
    print("❌ No farms found")
    exit(1)

print(f"Testing with farm: {farm.name}")

# Get weather data for this farm
weather_data = WeatherData.objects.filter(farm=farm).first()
if not weather_data:
    print("❌ No WeatherData found")
    exit(1)

print(f"✅ Found WeatherData")

# Build the weather dict like the view does
weather = {
    'temp': weather_data.temperature,
    'feels_like': weather_data.feels_like,
    'condition': weather_data.condition,
    'description': weather_data.description,
    'humidity': weather_data.humidity,
    'pressure': weather_data.pressure,
    'wind_speed': weather_data.wind_speed,
    'wind_direction': weather_data.wind_direction,
    'location': weather_data.location,
    'last_updated': weather_data.last_updated,
}

print("\n📊 Weather dict to be passed to template:")
for key, val in weather.items():
    print(f"  {key}: {val} (type: {type(val).__name__})")

# Parse forecast
from datetime import datetime
forecast = []
if weather_data.forecast_data.get('forecast'):
    forecast_raw = weather_data.forecast_data.get('forecast', [])
    print(f"\n📅 Forecast items in database: {len(forecast_raw)}")
    for i, item in enumerate(forecast_raw[:1]):  # Just show first item
        print(f"  Item {i}: {item}")
    
    for item in forecast_raw:
        try:
            date_str = item.get('date', '')
            if date_str:
                if isinstance(date_str, str):
                    day = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    day = datetime.fromtimestamp(date_str).date()
            else:
                continue
            
            forecast.append({
                'day': day,
                'temp_high': item.get('temp_high', 'N/A'),
                'temp_low': item.get('temp_low', 'N/A'),
                'condition': item.get('condition', 'Unknown'),
                'description': item.get('description', ''),
                'icon': item.get('icon', ''),
                'humidity': item.get('humidity', 'N/A'),
                'wind_speed': item.get('wind_speed', 'N/A'),
            })
        except (ValueError, TypeError) as e:
            print(f"  ❌ Error parsing: {e}")
            continue

print(f"\n✅ Forecast items parsed: {len(forecast)}")
for i, fc in enumerate(forecast[:2]):
    print(f"  Day {i}: {fc['day']} - {fc['temp_high']}°C high")

# Check what condition is checking
print(f"\n🔍 Template condition check:")
print(f"  weather.temp != 'N/A': {weather['temp'] != 'N/A'}")
print(f"  weather.temp value: {weather['temp']}")
print(f"  Evaluate to bool in template (would show data): {bool(weather['temp']) if weather['temp'] != 'N/A' else False}")

if weather['temp'] and weather['temp'] != 'N/A':
    print(f"  ✅ Should display: {weather['temp']}°C")
else:
    print(f"  ❌ Would show 'No Data Available'")
