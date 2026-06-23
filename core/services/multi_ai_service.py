# core/services/multi_ai_service.py
# Multi-Provider AI Service with Free Tier Support
# Supports Hugging Face, Replicate, Groq, Together, Gemini, and more

import logging
import os
import requests
from typing import Dict, List, Optional
from PIL import Image
import json
from io import BytesIO
from decouple import config

logger = logging.getLogger(__name__)


class MultiAIService:
    """
    Unified AI service supporting multiple free AI providers
    Automatic fallback between providers for reliability
    """
    
    def __init__(self):
        self.providers = {
            'huggingface': HuggingFaceProvider(),
            'replicate': ReplicateProvider(),
            'groq': GroqProvider(),
            'together': TogetherProvider(),
            'gemini': GeminiProvider(),
        }
        self.available_providers = []
        self._check_available_providers()
    
    def _check_available_providers(self):
        """Check which providers have valid API keys"""
        for name, provider in self.providers.items():
            if provider.is_available():
                self.available_providers.append(name)
                logger.info(f"[MULTI-AI] ✓ {name} provider available")
            else:
                logger.warning(f"[MULTI-AI] ✗ {name} provider not available (missing API key)")
        
        logger.info(f"[MULTI-AI] Available providers: {self.available_providers}")
    
    def detect_pest(self, image_file, provider_preference: Optional[str] = None) -> Dict:
        """
        Detect pests using available AI providers with automatic fallback
        """
        if not self.available_providers:
            logger.error("[MULTI-AI] No AI providers available")
            return self._get_fallback_response("No AI providers configured")
        
        # Try preferred provider first, then fallback to others
        providers_to_try = []
        if provider_preference and provider_preference in self.available_providers:
            providers_to_try.append(provider_preference)
        
        # Add remaining available providers
        for provider in self.available_providers:
            if provider not in providers_to_try:
                providers_to_try.append(provider)
        
        for provider_name in providers_to_try:
            try:
                logger.info(f"[MULTI-AI] Trying {provider_name} provider...")
                provider = self.providers[provider_name]
                result = provider.detect_pest(image_file)
                
                if result and result.get('success'):
                    logger.info(f"[MULTI-AI] ✓ Success with {provider_name}")
                    result['provider'] = provider_name
                    return result
                else:
                    logger.warning(f"[MULTI-AI] ✗ {provider_name} failed: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"[MULTI-AI] ✗ Error with {provider_name}: {str(e)}")
                continue
        
        # All providers failed
        logger.error("[MULTI-AI] All AI providers failed")
        return self._get_fallback_response("All AI providers failed")
    
    def _get_fallback_response(self, reason: str) -> Dict:
        """Return rule-based fallback response"""
        return {
            'success': False,
            'pest_name': 'Unknown',
            'confidence': 0,
            'treatment': 'Unable to analyze. Please try again or use manual inspection.',
            'error': reason,
            'provider': 'fallback'
        }


class HuggingFaceProvider:
    """Hugging Face Inference API (Free Tier)"""
    
    def __init__(self):
        self.api_key = config('HUGGINGFACE_API_KEY', default='')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.models = [
            'microsoft/resnet-50',  # Image classification
            'google/vit-base-patch16-224',  # Vision Transformer
        ]
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def detect_pest(self, image_file) -> Dict:
        try:
            # Convert image to bytes
            image_bytes = image_file.read()
            image_file.seek(0)
            
            # Try each model
            for model in self.models:
                try:
                    url = f"{self.base_url}/{model}"
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    response = requests.post(url, headers=headers, data=image_bytes)
                    
                    if response.status_code == 200:
                        predictions = response.json()
                        if predictions and len(predictions) > 0:
                            top_prediction = predictions[0]
                            return {
                                'success': True,
                                'pest_name': top_prediction.get('label', 'Unknown'),
                                'confidence': top_prediction.get('score', 0) * 100,
                                'treatment': self._get_treatment(top_prediction.get('label', 'Unknown')),
                            }
                except Exception as e:
                    logger.warning(f"[HUGGINGFACE] Model {model} failed: {str(e)}")
                    continue
            
            return {'success': False, 'error': 'All HuggingFace models failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_treatment(self, label: str) -> str:
        """Get treatment recommendation based on label"""
        treatments = {
            'aphid': 'Use neem oil spray or insecticidal soap. Introduce ladybugs.',
            'caterpillar': 'Hand-pick or use Bt (Bacillus thuringiensis) spray.',
            'mite': 'Use miticide or increase humidity to discourage mites.',
            'beetle': 'Use row covers or hand-pick. Consider neem oil.',
        }
        return treatments.get(label.lower(), 'Consult agricultural extension for specific treatment.')


class ReplicateProvider:
    """Replicate API (Free Tier Available)"""
    
    def __init__(self):
        self.api_key = config('REPLICATE_API_KEY', default='')
        self.models = [
            'salesforce/blip-2',  # Image captioning
            'openai/clip-vit-large-patch14',  # Image classification
        ]
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def detect_pest(self, image_file) -> Dict:
        try:
            # Replicate requires async API calls
            # This is a simplified implementation
            import replicate
            
            # Convert image to bytes
            image_bytes = image_file.read()
            image_file.seek(0)
            
            # Save temp file for Replicate
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            
            try:
                # Run model
                output = replicate.run(
                    "salesforce/blip-2:fl5c6d344d6a5c7b6b8c7b6b8c7b6b8c7b6b8c7b6b8c7b6b8c7b6b8c7b6b8c7b6",
                    input={"image": open(tmp_path, "rb")}
                )
                
                return {
                    'success': True,
                    'pest_name': output.get('caption', 'Unknown'),
                    'confidence': 85,
                    'treatment': self._get_treatment_from_caption(output.get('caption', '')),
                }
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_treatment_from_caption(self, caption: str) -> str:
        """Extract treatment from caption"""
        if 'healthy' in caption.lower():
            return 'No treatment needed. Continue regular monitoring.'
        elif 'disease' in caption.lower() or 'pest' in caption.lower():
            return 'Apply appropriate fungicide or pesticide. Consult local agricultural extension.'
        return 'Monitor closely and apply treatment if symptoms worsen.'


class GroqProvider:
    """Groq API (Fast, Free Tier)"""
    
    def __init__(self):
        self.api_key = config('GROQ_API_KEY', default='')
        self.base_url = "https://api.groq.com/openai/v1"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def detect_pest(self, image_file) -> Dict:
        try:
            # Groq supports vision through OpenAI-compatible API
            # This requires base64 encoding of image
            import base64
            
            image_bytes = image_file.read()
            image_file.seek(0)
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llava-v1.5-7b",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this agricultural image for pests or diseases. Identify the pest/disease name and suggest treatment."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {
                    'success': True,
                    'pest_name': self._extract_pest_name(content),
                    'confidence': 80,
                    'treatment': self._extract_treatment(content),
                }
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_pest_name(self, content: str) -> str:
        """Extract pest name from AI response"""
        # Simple extraction - can be improved with better parsing
        words = content.split()
        for word in words:
            if word.lower() in ['aphid', 'caterpillar', 'mite', 'beetle', 'fungus', 'mildew']:
                return word.capitalize()
        return 'Unknown'
    
    def _extract_treatment(self, content: str) -> str:
        """Extract treatment from AI response"""
        # Return full content as treatment for now
        return content[:500] if len(content) > 500 else content


class TogetherProvider:
    """Together AI (Free Tier)"""
    
    def __init__(self):
        self.api_key = config('TOGETHER_API_KEY', default='')
        self.base_url = "https://api.together.xyz/v1"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def detect_pest(self, image_file) -> Dict:
        try:
            import base64
            
            image_bytes = image_file.read()
            image_file.seek(0)
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/Llama-Vision-Free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Identify pests or diseases in this agricultural image"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {
                    'success': True,
                    'pest_name': self._extract_pest_name(content),
                    'confidence': 75,
                    'treatment': content[:500],
                }
            
            return {'success': False, 'error': f'API error: {response.status_code}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_pest_name(self, content: str) -> str:
        """Extract pest name from response"""
        words = content.split()
        for word in words:
            if word.lower() in ['aphid', 'caterpillar', 'mite', 'beetle', 'fungus']:
                return word.capitalize()
        return 'Unknown'


class GeminiProvider:
    """Google Gemini (Free Tier)"""
    
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
                logger.warning(f"[GEMINI] Initialization failed: {str(e)}")
    
    def is_available(self) -> bool:
        return self.available
    
    def detect_pest(self, image_file) -> Dict:
        try:
            from PIL import Image as PILImage
            
            image = PILImage.open(image_file)
            response = self.model.generate_content([
                "Analyze this agricultural image for pests or diseases. Identify the pest/disease and suggest treatment.",
                image
            ])
            
            content = response.text
            return {
                'success': True,
                'pest_name': self._extract_pest_name(content),
                'confidence': 85,
                'treatment': content[:500],
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_pest_name(self, content: str) -> str:
        """Extract pest name from response"""
        words = content.split()
        for word in words:
            if word.lower() in ['aphid', 'caterpillar', 'mite', 'beetle', 'fungus', 'mildew']:
                return word.capitalize()
        return 'Unknown'


# Singleton instance
multi_ai_service = MultiAIService()
