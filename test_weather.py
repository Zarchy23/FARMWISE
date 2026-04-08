#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import Farm, WeatherData
from django.conf import settings

print("=" * 70)
print("WEATHER DATA DEBUG")
print("=" * 70)

print(f"\nOPENWEATHER_API_KEY: {settings.OPENWEATHER_API_KEY[:20]}..." if settings.OPENWEATHER_API_KEY else "NOT SET")
print(f"WEATHER_API_URL: {settings.WEATHER_API_URL if hasattr(settings, 'WEATHER_API_URL') else 'NOT SET'}")

print("\n" + "=" * 70)
print("FARMS IN DATABASE")
print("=" * 70)
farms = Farm.objects.all()
if not farms.exists():
    print("No farms found!")
else:
    for farm in farms:
        print(f"\nFarm: {farm.name}")
        print(f"  Owner: {farm.owner.username}")
        print(f"  Latitude: {farm.latitude}")
        print(f"  Longitude: {farm.longitude}")
        print(f"  Has coordinates: {bool(farm.latitude and farm.longitude)}")

print("\n" + "=" * 70)
print("WEATHER DATA IN DATABASE")
print("=" * 70)
weather_data = WeatherData.objects.all()
if not weather_data.exists():
    print("No weather data found in database!")
else:
    for wd in weather_data:
        print(f"\nFarm: {wd.farm.name}")
        print(f"  Temperature: {wd.temperature}°C")
        print(f"  Condition: {wd.condition}")
        print(f"  Humidity: {wd.humidity}%")
        print(f"  Wind Speed: {wd.wind_speed} m/s")
        print(f"  Last Updated: {wd.last_updated}")

# Try to manually fetch weather data for testing
print("\n" + "=" * 70)
print("TEST: FETCHING WEATHER DATA")
print("=" * 70)

if settings.OPENWEATHER_API_KEY and farms.exists():
    import requests
    
    farm = farms.first()
    if farm.latitude and farm.longitude:
        print(f"\nTesting API call for {farm.name}...")
        print(f"Coordinates: {farm.latitude}, {farm.longitude}")
        
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={farm.latitude}&lon={farm.longitude}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
        
        try:
            response = requests.get(url, timeout=5)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ API call successful!")
                print(f"  City: {data.get('city', {}).get('name')}")
                print(f"  Country: {data.get('city', {}).get('country')}")
                if data.get('list'):
                    current = data['list'][0]
                    print(f"  Current Temp: {current['main']['temp']}°C")
                    print(f"  Condition: {current['weather'][0]['main']}")
            else:
                print(f"✗ API Error: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Request failed: {str(e)}")
    else:
        print("Farm missing coordinates!")
else:
    print("API key or farm not configured!")
