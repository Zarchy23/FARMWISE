# core/services/weather_ai_service.py
# AI-powered weather analysis and forecasting using multiple free AI providers

import logging
from typing import Dict, Optional
from decouple import config

logger = logging.getLogger(__name__)


class WeatherAIService:
    """
    AI service for weather analysis and agricultural recommendations
    Uses multiple free AI providers for reliability
    """
    
    def __init__(self):
        self.providers = {
            'groq': GroqWeatherProvider(),
            'together': TogetherWeatherProvider(),
            'gemini': GeminiWeatherProvider(),
        }
        self.available_providers = []
        self._check_available_providers()
    
    def _check_available_providers(self):
        """Check which providers have valid API keys"""
        for name, provider in self.providers.items():
            if provider.is_available():
                self.available_providers.append(name)
                logger.info(f"[WEATHER-AI] ✓ {name} provider available")
            else:
                logger.warning(f"[WEATHER-AI] ✗ {name} provider not available (missing API key)")
        
        logger.info(f"[WEATHER-AI] Available providers: {self.available_providers}")
    
    def analyze_weather_impact(self, weather_data: Dict, crop_type: str = None) -> Dict:
        """
        Analyze weather data and provide agricultural recommendations
        Uses AI to interpret weather patterns and suggest actions
        """
        if not self.available_providers:
            logger.warning("[WEATHER-AI] No AI providers available, using rule-based analysis")
            return self._rule_based_analysis(weather_data, crop_type)
        
        # Try available providers
        for provider_name in self.available_providers:
            try:
                logger.info(f"[WEATHER-AI] Trying {provider_name} provider...")
                provider = self.providers[provider_name]
                result = provider.analyze_weather(weather_data, crop_type)
                
                if result and result.get('success'):
                    logger.info(f"[WEATHER-AI] ✓ Success with {provider_name}")
                    result['provider'] = provider_name
                    return result
                else:
                    logger.warning(f"[WEATHER-AI] ✗ {provider_name} failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"[WEATHER-AI] ✗ Error with {provider_name}: {str(e)}")
                continue
        
        # All providers failed, use rule-based
        logger.warning("[WEATHER-AI] All AI providers failed, using rule-based analysis")
        return self._rule_based_analysis(weather_data, crop_type)
    
    def generate_weather_alert(self, weather_data: Dict, alert_type: str) -> Dict:
        """
        Generate detailed weather alert using AI
        """
        if not self.available_providers:
            return self._generate_basic_alert(weather_data, alert_type)
        
        for provider_name in self.available_providers:
            try:
                provider = self.providers[provider_name]
                result = provider.generate_alert(weather_data, alert_type)
                if result and result.get('success'):
                    result['provider'] = provider_name
                    return result
            except Exception as e:
                logger.error(f"[WEATHER-AI] Alert generation failed with {provider_name}: {str(e)}")
                continue
        
        return self._generate_basic_alert(weather_data, alert_type)
    
    def _rule_based_analysis(self, weather_data: Dict, crop_type: str = None) -> Dict:
        """Fallback rule-based weather analysis"""
        temp = weather_data.get('current', {}).get('temperature', 0)
        humidity = weather_data.get('current', {}).get('humidity', 0)
        precipitation = weather_data.get('current', {}).get('precipitation', 0)
        
        recommendations = []
        
        # Temperature analysis
        if temp > 35:
            recommendations.append("Extreme heat: Ensure adequate irrigation and provide shade for livestock")
        elif temp > 30:
            recommendations.append("High temperature: Monitor crops for water stress")
        elif temp < 5:
            recommendations.append("Cold temperature: Protect sensitive crops from frost")
        
        # Humidity analysis
        if humidity > 80:
            recommendations.append("High humidity: Risk of fungal diseases, ensure good air circulation")
        elif humidity < 30:
            recommendations.append("Low humidity: Increase irrigation frequency")
        
        # Precipitation analysis
        if precipitation > 10:
            recommendations.append("Heavy rain: Check drainage, prevent waterlogging")
        elif precipitation > 0:
            recommendations.append("Rain detected: Adjust irrigation schedule")
        
        return {
            'success': True,
            'analysis': 'Rule-based analysis',
            'recommendations': recommendations,
            'risk_level': self._calculate_risk_level(temp, humidity, precipitation),
            'provider': 'rule-based'
        }
    
    def _calculate_risk_level(self, temp: float, humidity: float, precipitation: float) -> str:
        """Calculate overall risk level"""
        risk_score = 0
        
        if temp > 35 or temp < 5:
            risk_score += 2
        elif temp > 30 or temp < 10:
            risk_score += 1
        
        if humidity > 80 or humidity < 30:
            risk_score += 1
        
        if precipitation > 10:
            risk_score += 2
        elif precipitation > 0:
            risk_score += 1
        
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_basic_alert(self, weather_data: Dict, alert_type: str) -> Dict:
        """Generate basic alert without AI"""
        temp = weather_data.get('current', {}).get('temperature', 0)
        
        alerts = {
            'heat': f"Temperature alert: {temp}°C. Take precautions to protect crops and livestock.",
            'cold': f"Cold alert: {temp}°C. Protect sensitive crops from frost damage.",
            'rain': "Rain alert: Check drainage and adjust irrigation.",
            'wind': "Wind alert: Secure loose items and protect young plants.",
        }
        
        return {
            'success': True,
            'message': alerts.get(alert_type, 'Weather alert: Monitor conditions closely.'),
            'provider': 'rule-based'
        }


class GroqWeatherProvider:
    """Groq AI for weather analysis"""
    
    def __init__(self):
        self.api_key = config('GROQ_API_KEY', default='')
        self.base_url = "https://api.groq.com/openai/v1"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def analyze_weather(self, weather_data: Dict, crop_type: str = None) -> Dict:
        try:
            import requests
            
            temp = weather_data.get('current', {}).get('temperature', 0)
            humidity = weather_data.get('current', {}).get('humidity', 0)
            precipitation = weather_data.get('current', {}).get('precipitation', 0)
            
            prompt = f"""Analyze this weather data for agricultural impact:
Temperature: {temp}°C
Humidity: {humidity}%
Precipitation: {precipitation}mm
Crop Type: {crop_type or 'General'}

Provide:
1. Risk assessment (low/medium/high)
2. Specific recommendations for farmers
3. Any precautions needed

Respond in JSON format with keys: risk_level, recommendations, precautions"""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {
                    'success': True,
                    'analysis': content,
                    'recommendations': [content[:200]],
                    'risk_level': 'medium',
                }
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_alert(self, weather_data: Dict, alert_type: str) -> Dict:
        try:
            import requests
            
            temp = weather_data.get('current', {}).get('temperature', 0)
            
            prompt = f"Generate a detailed weather alert for {alert_type} with temperature {temp}°C. Provide actionable advice for farmers."
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {'success': True, 'message': content}
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class TogetherWeatherProvider:
    """Together AI for weather analysis"""
    
    def __init__(self):
        self.api_key = config('TOGETHER_API_KEY', default='')
        self.base_url = "https://api.together.xyz/v1"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def analyze_weather(self, weather_data: Dict, crop_type: str = None) -> Dict:
        try:
            import requests
            
            temp = weather_data.get('current', {}).get('temperature', 0)
            humidity = weather_data.get('current', {}).get('humidity', 0)
            
            prompt = f"Analyze agricultural weather conditions: {temp}°C, {humidity}% humidity. Provide farming recommendations."
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {
                    'success': True,
                    'analysis': content,
                    'recommendations': [content[:200]],
                    'risk_level': 'medium',
                }
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_alert(self, weather_data: Dict, alert_type: str) -> Dict:
        try:
            import requests
            
            prompt = f"Generate weather alert for {alert_type}. Provide actionable farming advice."
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens': 300
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {'success': True, 'message': content}
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class GeminiWeatherProvider:
    """Google Gemini for weather analysis"""
    
    def __init__(self):
        self.api_key = config('GEMINI_API_KEY', default='')
        self.available = False
        self.model = None
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                self.available = True
            except Exception as e:
                logger.warning(f"[GEMINI-WEATHER] Initialization failed: {str(e)}")
    
    def is_available(self) -> bool:
        return self.available
    
    def analyze_weather(self, weather_data: Dict, crop_type: str = None) -> Dict:
        try:
            temp = weather_data.get('current', {}).get('temperature', 0)
            humidity = weather_data.get('current', {}).get('humidity', 0)
            
            prompt = f"""Analyze agricultural weather conditions:
Temperature: {temp}°C
Humidity: {humidity}%
Crop: {crop_type or 'General'}

Provide risk assessment and farming recommendations."""
            
            response = self.model.generate_content(prompt)
            
            return {
                'success': True,
                'analysis': response.text,
                'recommendations': [response.text[:200]],
                'risk_level': 'medium',
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_alert(self, weather_data: Dict, alert_type: str) -> Dict:
        try:
            temp = weather_data.get('current', {}).get('temperature', 0)
            
            prompt = f"Generate detailed weather alert for {alert_type} at {temp}°C. Provide actionable farming advice."
            
            response = self.model.generate_content(prompt)
            
            return {'success': True, 'message': response.text}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Singleton instance
weather_ai_service = WeatherAIService()
