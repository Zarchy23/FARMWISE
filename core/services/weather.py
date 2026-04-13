# core/services/weather.py
# FREE weather service using Open-Meteo - NO API KEY NEEDED!
# Works perfectly on Render free tier!

import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class OpenMeteoWeatherService:
    """
    Free weather service for FarmWise using Open-Meteo API
    - No API key required
    - Unlimited calls
    - Works on Render free tier
    - Includes agricultural indicators
    """
    
    BASE_URL = "https://api.open-meteo.com/v1"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def get_forecast(self, lat: float, lng: float, days: int = 7) -> Dict:
        """
        Get weather forecast for a location
        
        Agricultural indicators automatically included:
        - Temperature-Humidity Index (THI) for livestock stress
        - Growing Degree Days (GDD) for crop development
        - Frost risk for crop protection
        """
        cache_key = f"weather_forecast_{lat}_{lng}_{days}"
        
        # Try to get from cache, but don't fail if Redis is unavailable
        try:
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Weather forecast loaded from cache for {lat},{lng}")
                return cached
        except Exception as cache_error:
            logger.warning(f"Cache unavailable: {cache_error}. Fetching fresh data.")
        
        try:
            params = {
                "latitude": lat,
                "longitude": lng,
                "hourly": [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation",
                    "wind_speed_10m",
                    "soil_temperature_0cm"
                ],
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "wind_speed_10m_max",
                    "sunrise",
                    "sunset"
                ],
                "forecast_days": days,
                "timezone": "auto"
            }
            
            logger.info(f"Fetching weather from Open-Meteo for {lat},{lng}")
            response = self.client.get(f"{self.BASE_URL}/forecast", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Add agricultural indicators
            data = self._add_agricultural_indicators(data, lat, lng)
            
            # Try to cache for 1 hour, but don't fail if Redis is unavailable
            try:
                cache.set(cache_key, data, 3600)
                logger.info(f"Weather forecast cached successfully")
            except Exception as cache_error:
                logger.warning(f"Cache set failed: {cache_error}. Data still returned.")
            
            return data
            
        except Exception as e:
            logger.error(f"Weather fetch error for {lat},{lng}: {str(e)}")
            return self._get_error_response(str(e))
    
    def get_agricultural_forecast(self, lat: float, lng: float) -> Dict:
        """
        Get agriculture-specific forecast
        Includes crop stress indicators and pest risk
        """
        cache_key = f"ag_forecast_{lat}_{lng}"
        
        # Try to get from cache, but don't fail if Redis is unavailable
        try:
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Agricultural forecast loaded from cache")
                return cached
        except Exception as cache_error:
            logger.warning(f"Cache unavailable: {cache_error}. Fetching fresh data.")
        
        try:
            # Get base weather
            weather = self.get_forecast(lat, lng, days=7)
            
            if 'error' in weather:
                return weather
            
            # Calculate agricultural metrics
            ag_metrics = []
            daily_times = weather.get('daily', {}).get('time', [])
            daily_temps_max = weather.get('daily', {}).get('temperature_2m_max', [])
            daily_temps_min = weather.get('daily', {}).get('temperature_2m_min', [])
            hourly_humidity = weather.get('hourly', {}).get('relative_humidity_2m', [])
            
            for i, day in enumerate(daily_times):
                if i >= len(daily_temps_max) or i >= len(daily_temps_min):
                    break
                
                temp_max = daily_temps_max[i]
                temp_min = daily_temps_min[i]
                humidity = hourly_humidity[i*24] if i*24 < len(hourly_humidity) else 50
                
                # Growing Degree Days (base 10°C for maize)
                gdd = max(0, (temp_max + temp_min) / 2 - 10)
                
                # Temperature-Humidity Index (livestock stress)
                thi = 0.8 * temp_max + (humidity / 100) * (temp_max - 14.4) + 46.4
                
                # Heat stress classification
                if thi > 78:
                    heat_stress = "🔥 Severe - Take action"
                elif thi > 72:
                    heat_stress = "⚠️ Moderate - Monitor livestock"
                else:
                    heat_stress = "✅ Normal"
                
                # Frost risk
                frost_risk = temp_min < 2
                
                ag_metrics.append({
                    "date": day,
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "humidity": humidity,
                    "growing_degree_days": round(gdd, 1),
                    "temperature_humidity_index": round(thi, 1),
                    "heat_stress": heat_stress,
                    "frost_risk": frost_risk,
                    "recommendation": self._get_farming_recommendation(temp_max, temp_min, humidity, frost_risk)
                })
            
            result = {
                "status": "success",
                "location": {"lat": lat, "lng": lng},
                "forecast": ag_metrics,
                "alerts": self._check_alerts(weather)
            }
            
            # Try to cache for 1 hour, but don't fail if Redis is unavailable
            try:
                cache.set(cache_key, result, 3600)
                logger.info(f"Agricultural forecast generated successfully")
            except Exception as cache_error:
                logger.warning(f"Cache set failed: {cache_error}. Data still returned.")
            
            return result
            
        except Exception as e:
            logger.error(f"Agricultural forecast error: {str(e)}")
            return self._get_error_response(str(e))
    
    def get_historical_weather(self, lat: float, lng: float, start_date: str, end_date: str) -> Dict:
        """
        Get historical weather data for yield analysis
        Free tier includes 80+ years of historical data!
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lng,
                "start_date": start_date,
                "end_date": end_date,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "rain_days"
                ],
                "timezone": "auto"
            }
            
            logger.info(f"Fetching historical weather from {start_date} to {end_date}")
            response = self.client.get(f"{self.BASE_URL}/archive", params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Historical weather fetched successfully")
            
            return data
            
        except Exception as e:
            logger.error(f"Historical weather fetch error: {str(e)}")
            return self._get_error_response(str(e))
    
    def _add_agricultural_indicators(self, data: Dict, lat: float, lng: float) -> Dict:
        """Add THI, GDD, and other agricultural metrics"""
        if 'daily' not in data:
            return data
        
        agricultural = []
        daily_times = data['daily'].get('time', [])
        daily_temps_max = data['daily'].get('temperature_2m_max', [])
        daily_temps_min = data['daily'].get('temperature_2m_min', [])
        
        for i, day in enumerate(daily_times):
            if i >= len(daily_temps_max) or i >= len(daily_temps_min):
                break
            
            temp_max = daily_temps_max[i]
            temp_min = daily_temps_min[i]
            
            # Growing Degree Days (for crop development, base 10°C)
            gdd = max(0, (temp_max + temp_min) / 2 - 10)
            
            # Simple pest risk indicator
            pest_risk = "High" if 25 <= temp_max <= 35 else "Low"
            
            agricultural.append({
                "date": day,
                "growing_degree_days": round(gdd, 1),
                "pest_risk": pest_risk
            })
        
        data['agricultural_indicators'] = agricultural
        return data
    
    def _get_farming_recommendation(self, temp_max: float, temp_min: float, humidity: float, frost_risk: bool) -> str:
        """Generate actionable farming recommendations"""
        if frost_risk:
            return "❄️ Frost risk tonight! Cover sensitive crops and move livestock indoors."
        elif temp_max > 32:
            return "🔥 Extreme heat! Ensure livestock have shade and water. Avoid midday fieldwork."
        elif temp_max > 28:
            return "☀️ Hot conditions. Water crops in early morning. Monitor livestock for heat stress."
        elif humidity > 80 and temp_max > 20:
            return "💧 High humidity - disease risk. Consider preventive fungicide application."
        elif temp_min < 10:
            return "🌡️ Cool nights. Delay planting of warm-season crops."
        else:
            return "✅ Favorable conditions for farming activities."
    
    def _check_alerts(self, weather: Dict) -> List[Dict]:
        """Generate weather alerts for farmers"""
        alerts = []
        
        if 'daily' in weather:
            daily_times = weather['daily'].get('time', [])
            temps_min = weather['daily'].get('temperature_2m_min', [])
            temps_max = weather['daily'].get('temperature_2m_max', [])
            
            for i, temp_min in enumerate(temps_min):
                if temp_min < 2:
                    alerts.append({
                        "type": "frost",
                        "date": daily_times[i] if i < len(daily_times) else "",
                        "severity": "warning",
                        "message": f"❄️ Frost expected! Protect crops."
                    })
            
            for i, temp_max in enumerate(temps_max):
                if temp_max > 35:
                    alerts.append({
                        "type": "heatwave",
                        "date": daily_times[i] if i < len(daily_times) else "",
                        "severity": "warning",
                        "message": f"🔥 Extreme heat! Ensure livestock welfare."
                    })
        
        return alerts
    
    def _get_error_response(self, error_msg: str) -> Dict:
        """Return error response with helpful message"""
        return {
            "error": error_msg,
            "status": "error",
            "message": "Failed to fetch weather data. Please try again later.",
            "forecast": [],
            "alerts": []
        }


# Singleton instance
weather_service = OpenMeteoWeatherService()
