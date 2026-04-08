#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Farm, WeatherData
from django.conf import settings
import requests

print("Fetching weather data...")

api_key = settings.OPENWEATHER_API_KEY
farms = Farm.objects.all()

for farm in farms:
    if not (farm.latitude and farm.longitude):
        print(f"Skipping {farm.name} - missing coordinates")
        continue
    
    try:
        print(f"\nFetching weather for {farm.name}...")
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={farm.latitude}&lon={farm.longitude}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('list') and len(data['list']) > 0:
            current = data['list'][0]
            main = current['main']
            weather = current['weather'][0]
            wind = current.get('wind', {})
            clouds = current.get('clouds', {})
            
            # Prepare forecast data (next 5 days)
            forecast_list = []
            for i in range(0, min(40, len(data['list'])), 8):  # Every 24 hours
                forecast_entry = data['list'][i]
                forecast_list.append({
                    'date': forecast_entry['dt'],
                    'temp_high': forecast_entry['main']['temp_max'],
                    'temp_low': forecast_entry['main']['temp_min'],
                    'condition': forecast_entry['weather'][0]['main'],
                    'description': forecast_entry['weather'][0]['description'],
                    'icon': forecast_entry['weather'][0]['icon'],
                    'humidity': forecast_entry['main']['humidity'],
                    'wind_speed': forecast_entry['wind'].get('speed', 0),
                })
            
            # Update or create WeatherData
            weather_obj, created = WeatherData.objects.update_or_create(
                farm=farm,
                defaults={
                    'temperature': main['temp'],
                    'feels_like': main.get('feels_like'),
                    'humidity': main['humidity'],
                    'pressure': main.get('pressure'),
                    'wind_speed': wind.get('speed', 0),
                    'wind_direction': wind.get('deg'),
                    'cloudiness': clouds.get('all'),
                    'condition': weather['main'],
                    'description': weather['description'],
                    'icon': weather['icon'],
                    'forecast_data': {'forecast': forecast_list},
                    'location': f"{data['city']['name']}, {data['city']['country']}",
                }
            )
            
            print(f"✓ Updated weather for {farm.name}")
            print(f"  Temperature: {main['temp']}°C")
            print(f"  Condition: {weather['main']}")
            print(f"  Humidity: {main['humidity']}%")
            
    except Exception as e:
        print(f"✗ Failed to fetch weather for {farm.name}: {str(e)}")

print("\n" + "=" * 70)
print("WEATHER DATA IN DATABASE NOW")
print("=" * 70)
for wd in WeatherData.objects.all():
    print(f"\nFarm: {wd.farm.name}")
    print(f"  Temperature: {wd.temperature}°C")
    print(f"  Condition: {wd.condition}")
    print(f"  Humidity: {wd.humidity}%")
    print(f"  Wind Speed: {wd.wind_speed} m/s")
    print(f"  Last Updated: {wd.last_updated}")
