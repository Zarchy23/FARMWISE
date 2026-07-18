"""
Hybrid Prediction Service
Combines local ML models with external AI APIs for advanced results
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HybridPredictionService:
    """Service that combines local models with external AI APIs"""

    def __init__(self):
        self.ml_service = None
        self.multi_ai_available = False

        # Try to import multi-AI service
        try:
            from .multi_ai_service import multi_ai_service
            self.multi_ai_service = multi_ai_service
            self.multi_ai_available = True
            logger.info("Hybrid service: Multi-AI service available")
        except ImportError:
            logger.warning("Hybrid service: Multi-AI service not available")

    def _get_ml_service(self):
        """Lazy load ML service"""
        if self.ml_service is None:
            try:
                from .ml_model_service import ml_service
                self.ml_service = ml_service
            except Exception as e:
                logger.warning(f"Could not load ML service: {e}")
                self.ml_service = None
        return self.ml_service
    
    def predict_pest_hybrid(self, image_path: str, use_api_fallback: bool = True) -> Dict:
        """
        Hybrid pest prediction using local model + external AI
        
        Args:
            image_path: Path to image file
            use_api_fallback: Whether to use external AI as fallback
        
        Returns:
            Combined prediction results
        """
        results = {
            'local_model': None,
            'external_ai': None,
            'combined': None,
            'confidence': 0.0,
            'pest_name': 'Unknown',
            'pest_detected': False
        }
        
        # Try local model first
        try:
            ml_service = self._get_ml_service()
            if ml_service:
                local_result = ml_service.predict_pest(image_path)
                if 'error' not in local_result:
                    results['local_model'] = local_result
                    results['pest_name'] = local_result.get('pest', 'Unknown')
                    results['confidence'] = local_result.get('confidence', 0.0)
                    results['pest_detected'] = local_result.get('confidence', 0.0) > 0.5
                    logger.info(f"Local pest model: {local_result.get('pest')} ({local_result.get('confidence', 0):.2f})")
        except Exception as e:
            logger.warning(f"Local pest model failed: {e}")
        
        # Try external AI if enabled and fallback requested
        if use_api_fallback and self.multi_ai_available:
            try:
                from PIL import Image
                image = Image.open(image_path)
                # Call external AI service
                external_result = self._call_external_pest_ai(image)
                if external_result:
                    results['external_ai'] = external_result
                    logger.info(f"External AI pest: {external_result.get('detected_issue')}")
                    
                    # Combine results
                    results['combined'] = self._combine_pest_results(
                        results['local_model'], 
                        external_result
                    )
            except Exception as e:
                logger.warning(f"External AI pest failed: {e}")
        
        # Use best available result
        if results['combined']:
            return results['combined']
        elif results['local_model']:
            return self._format_pest_result(results['local_model'])
        elif results['external_ai']:
            return results['external_ai']
        else:
            return {'error': 'All prediction methods failed'}
    
    def predict_disease_hybrid(self, image_path: str, use_api_fallback: bool = True) -> Dict:
        """
        Hybrid disease prediction using local model + external AI
        
        Args:
            image_path: Path to image file
            use_api_fallback: Whether to use external AI as fallback
        
        Returns:
            Combined prediction results
        """
        results = {
            'local_model': None,
            'external_ai': None,
            'combined': None,
            'confidence': 0.0,
            'disease_name': 'Unknown',
            'disease_detected': False
        }
        
        # Try local model first
        try:
            ml_service = self._get_ml_service()
            if ml_service:
                local_result = ml_service.predict_disease(image_path)
                if 'error' not in local_result:
                    results['local_model'] = local_result
                    results['disease_name'] = local_result.get('disease', 'Unknown')
                    results['confidence'] = local_result.get('confidence', 0.0)
                    results['disease_detected'] = local_result.get('confidence', 0.0) > 0.5
                    logger.info(f"Local disease model: {local_result.get('disease')} ({local_result.get('confidence', 0):.2f})")
        except Exception as e:
            logger.warning(f"Local disease model failed: {e}")
        
        # Try external AI if enabled and fallback requested
        if use_api_fallback and self.multi_ai_available:
            try:
                from PIL import Image
                image = Image.open(image_path)
                # Call external AI service
                external_result = self._call_external_disease_ai(image)
                if external_result:
                    results['external_ai'] = external_result
                    logger.info(f"External AI disease: {external_result.get('detected_issue')}")
                    
                    # Combine results
                    results['combined'] = self._combine_disease_results(
                        results['local_model'], 
                        external_result
                    )
            except Exception as e:
                logger.warning(f"External AI disease failed: {e}")
        
        # Use best available result
        if results['combined']:
            return results['combined']
        elif results['local_model']:
            return self._format_disease_result(results['local_model'])
        elif results['external_ai']:
            return results['external_ai']
        else:
            return {'error': 'All prediction methods failed'}
    
    def predict_yield_hybrid(self, features: Dict, use_api_fallback: bool = True) -> Dict:
        """
        Hybrid yield prediction using local model + external AI
        
        Args:
            features: Feature dictionary
            use_api_fallback: Whether to use external AI as fallback
        
        Returns:
            Combined prediction results
        """
        results = {
            'local_model': None,
            'external_ai': None,
            'combined': None,
            'predicted_yield': 0.0
        }
        
        # Try local model first
        try:
            ml_service = self._get_ml_service()
            if ml_service:
                local_result = ml_service.predict_yield(features)
                if 'error' not in local_result:
                    results['local_model'] = local_result
                    results['predicted_yield'] = local_result.get('predicted_yield_kg_per_hectare', 0.0)
                    logger.info(f"Local yield model: {results['predicted_yield']:.2f} kg/ha")
        except Exception as e:
            logger.warning(f"Local yield model failed: {e}")
        
        # Try external AI if enabled and fallback requested
        if use_api_fallback and self.multi_ai_available:
            try:
                # Call external AI service for yield prediction
                external_result = self._call_external_yield_ai(features)
                if external_result:
                    results['external_ai'] = external_result
                    logger.info(f"External AI yield: {external_result.get('predicted_yield', 0):.2f} kg/ha")
                    
                    # Combine results (average)
                    if results['local_model']:
                        local_yield = results['local_model'].get('predicted_yield_kg_per_hectare', 0)
                        external_yield = external_result.get('predicted_yield', 0)
                        combined_yield = (local_yield + external_yield) / 2
                        results['combined'] = {
                            'predicted_yield_kg_per_hectare': combined_yield,
                            'local_yield': local_yield,
                            'external_yield': external_yield,
                            'method': 'hybrid_average'
                        }
            except Exception as e:
                logger.warning(f"External AI yield failed: {e}")
        
        # Use best available result
        if results['combined']:
            return results['combined']
        elif results['local_model']:
            return results['local_model']
        elif results['external_ai']:
            return results['external_ai']
        else:
            return {'error': 'All prediction methods failed'}
    
    def _call_external_pest_ai(self, image) -> Optional[Dict]:
        """Call external AI for pest detection"""
        try:
            # Use existing pest detection service
            from .pest_detection import PestDetectionService
            from decouple import config
            
            gemini_key = config('GEMINI_API_KEY', default='')
            groq_key = config('GROQ_API_KEY', default='')
            openai_key = config('OPENAI_API_KEY', default='')
            
            if not gemini_key and not groq_key and not openai_key:
                return None
            
            pest_service = PestDetectionService(gemini_key, groq_key, openai_key)
            
            # Convert PIL image to file-like object
            from io import BytesIO
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            result = pest_service.detect_from_image(img_buffer)
            return result
        except Exception as e:
            logger.error(f"External pest AI error: {e}")
            return None
    
    def _call_external_disease_ai(self, image) -> Optional[Dict]:
        """Call external AI for disease detection"""
        try:
            # Use existing disease detection service
            from .disease_service import DiseaseDetectionService
            from decouple import config
            
            gemini_key = config('GEMINI_API_KEY', default='')
            
            if not gemini_key:
                return None
            
            disease_service = DiseaseDetectionService(gemini_key)
            
            # Convert PIL image to file-like object
            from io import BytesIO
            img_buffer = BytesIO()
            image.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            result = disease_service.detect_from_image(img_buffer)
            return result
        except Exception as e:
            logger.error(f"External disease AI error: {e}")
            return None
    
    def _call_external_yield_ai(self, features: Dict) -> Optional[Dict]:
        """Call external AI for yield prediction"""
        try:
            if not self.multi_ai_available:
                return None
            
            # Create prompt for AI
            prompt = f"""
            Based on these agricultural features, predict crop yield in kg/hectare:
            Area: {features.get('area_hectares', 0)} hectares
            Soil Nitrogen: {features.get('soil_nitrogen', 0)} mg/kg
            Soil Phosphorus: {features.get('soil_phosphorus', 0)} mg/kg
            Soil Potassium: {features.get('soil_potassium', 0)} mg/kg
            Soil pH: {features.get('soil_ph', 0)}
            Temperature: {features.get('temperature_avg', 0)}°C
            Rainfall: {features.get('rainfall_mm', 0)} mm
            Humidity: {features.get('humidity', 0)}%
            Fertilizer: {features.get('fertilizer_kg_ha', 0)} kg/ha
            Irrigation: {features.get('irrigation_days', 0)} days
            Pesticide: {features.get('pesticide_used', 0)}
            Disease Severity: {features.get('disease_severity', 0)}
            
            Return only the predicted yield number in kg/hectare.
            """
            
            # Call AI service
            response = self.multi_ai_service.generate_response(prompt)
            
            # Extract number from response
            import re
            numbers = re.findall(r'\d+\.?\d*', response)
            if numbers:
                predicted_yield = float(numbers[0])
                return {'predicted_yield': predicted_yield, 'method': 'external_ai'}
            
        except Exception as e:
            logger.error(f"External yield AI error: {e}")
            return None
    
    def _combine_pest_results(self, local_result: Dict, external_result: Dict) -> Dict:
        """Combine local and external pest results"""
        # Weight local model higher if confidence is high
        local_confidence = local_result.get('confidence', 0.0)
        
        if local_confidence > 0.7:
            # Trust local model more
            return self._format_pest_result(local_result)
        else:
            # Use external AI result
            return external_result
    
    def _combine_disease_results(self, local_result: Dict, external_result: Dict) -> Dict:
        """Combine local and external disease results"""
        # Weight local model higher if confidence is high
        local_confidence = local_result.get('confidence', 0.0)
        
        if local_confidence > 0.7:
            # Trust local model more
            return self._format_disease_result(local_result)
        else:
            # Use external AI result
            return external_result
    
    def _format_pest_result(self, local_result: Dict) -> Dict:
        """Format local pest result to match external format"""
        return {
            'pest_detected': local_result.get('confidence', 0.0) > 0.5,
            'pest_name': local_result.get('pest', 'Unknown'),
            'confidence': local_result.get('confidence', 0.0) * 100,
            'method': 'local_model',
            'class_index': local_result.get('class_index', -1)
        }
    
    def _format_disease_result(self, local_result: Dict) -> Dict:
        """Format local disease result to match external format"""
        return {
            'disease_detected': local_result.get('confidence', 0.0) > 0.5,
            'disease_name': local_result.get('disease', 'Unknown'),
            'confidence': local_result.get('confidence', 0.0) * 100,
            'method': 'local_model',
            'class_index': local_result.get('class_index', -1)
        }


# Singleton instance
hybrid_service = HybridPredictionService()
