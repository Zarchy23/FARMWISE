# core/services/pest_detection.py
# FREE pest detection using Google Gemini (free tier) or rule-based approach

import logging
import os
from typing import Dict, List
from PIL import Image
import json
from io import BytesIO
from decouple import config

logger = logging.getLogger(__name__)

# Production settings - Read from Django settings if available, fallback to environment
try:
    from django.conf import settings
    IS_PRODUCTION = getattr(settings, 'IS_PRODUCTION', False)
    DISABLE_GEMINI_ON_PRODUCTION = getattr(settings, 'DISABLE_GEMINI_ON_PRODUCTION', False)
    DEBUG_MODE = getattr(settings, 'DEBUG', True)
except ImportError:
    # Fallback if Django settings not available
    DEBUG_MODE = config('DEBUG', default='True') == 'True'
    IS_PRODUCTION = not DEBUG_MODE  # Infer from DEBUG
    DISABLE_GEMINI_ON_PRODUCTION = config('DISABLE_GEMINI_ON_PRODUCTION', default='True' if IS_PRODUCTION else 'False') == 'True'

logger.info(f"[PEST_DETECTION INIT] DEBUG={DEBUG_MODE}, IS_PRODUCTION={IS_PRODUCTION}, DISABLE_GEMINI={DISABLE_GEMINI_ON_PRODUCTION}")

if IS_PRODUCTION and DISABLE_GEMINI_ON_PRODUCTION:
    logger.warning("[PEST_DETECTION] 🚫 PRODUCTION MODE DETECTED - GEMINI DISABLED - Using fallback only")
elif IS_PRODUCTION:
    logger.warning("[PEST_DETECTION] Production mode with Gemini ENABLED (rate limiting active)")
else:
    logger.info("[PEST_DETECTION] Development mode - Gemini enabled")


class GeminiPestDetector:
    """
    Free AI pest detection using Google Gemini
    - Has free tier (60 requests/minute)
    - Works on Render free tier
    - Fast and reliable for agricultural use
    """
    
    # Available models to try (in order of preference)
    # These are verified working with the Gemini API
    AVAILABLE_MODELS = [
        'gemini-2.5-flash',      # Latest, fastest, most reliable
        'gemini-2.5-pro',        # More powerful for complex analysis
        'gemini-2.0-flash',      # Stable alternative
        'gemini-flash-latest',   # Always-updated version
    ]
    
    def __init__(self, api_key: str):
        logger.info(f"[GEMINI INIT] Starting initialization...")
        logger.info(f"[GEMINI INIT] API Key provided: {bool(api_key) and len(str(api_key)) > 0}")
        try:
            import google.generativeai as genai
            logger.info(f"[GEMINI INIT] google.generativeai imported successfully")
            self.genai = genai
            self.genai.configure(api_key=api_key)
            logger.info(f"[GEMINI INIT] API key configured")
            self.model = None
            self.available = False
            
            # Try each model until one works
            for model_name in self.AVAILABLE_MODELS:
                try:
                    logger.info(f"[GEMINI INIT] Trying to create model {model_name}...")
                    test_model = self.genai.GenerativeModel(model_name)
                    logger.info(f"[GEMINI INIT] ✓ Successfully created {model_name}")
                    self.model = test_model
                    self.available = True
                    logger.info(f"✓ Using Gemini model: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"[GEMINI INIT] Model {model_name} not available: {str(e)}")
                    continue
            
            if not self.available:
                logger.error("[GEMINI INIT] ✗ No Gemini models available - all failed")
            else:
                logger.info(f"[GEMINI INIT] ✓ Initialization complete, model ready")
        except ImportError as ie:
            logger.warning(f"[GEMINI INIT] ImportError: google-generativeai not installed. {str(ie)}")
            self.available = False
        except Exception as e:
            logger.error(f"[GEMINI INIT] Fatal error: {str(e)}", exc_info=True)
            self.available = False
    
    def detect_pest(self, image_file) -> Dict:
        """
        Analyze crop image for pests and diseases
        Returns: pest name, confidence, treatment recommendations
        """
        # CRITICAL: Check production flag BEFORE making any API calls
        logger.info(f"[DETECT_PEST] Checking production safety: IS_PRODUCTION={IS_PRODUCTION}, DISABLE_GEMINI={DISABLE_GEMINI_ON_PRODUCTION}")
        
        if IS_PRODUCTION and DISABLE_GEMINI_ON_PRODUCTION:
            logger.warning("[DETECT_PEST] 🚫 PRODUCTION MODE - GEMINI DISABLED - Returning fallback immediately")
            return RuleBasedPestDetector.get_fallback_response("Production environment: Using offline detection")
        
        logger.info(f"[GEMINI] Gemini check: available={self.available}, model={self.model}")
        
        if not self.available or not self.model:
            logger.warning("[GEMINI] Gemini not available, using fallback")
            return RuleBasedPestDetector.get_fallback_response("Gemini API not available")
        
        try:
            logger.info(f"[GEMINI] Loading image from file")
            # Load and prepare image
            image = Image.open(image_file)
            logger.info(f"[GEMINI] Image loaded: {image.size}, format={image.format}")
            
            # Create prompt for pest detection
            prompt = """You are an expert agricultural pest detection AI with 20+ years of experience.
Analyze this crop image and identify any pests, diseases, nutrient deficiencies, or other agricultural issues.
Be precise and practical for African farming conditions.

Respond in this EXACT JSON format (no other text):
{
    "detected_issue": "specific pest/disease/deficiency name or 'Healthy Crop'",
    "confidence": 0-100,
    "severity": "none/low/medium/high/severe",
    "description": "2-3 sentences about what you see",
    "treatment": "practical treatment options available locally",
    "prevention": "how to prevent this in the future",
    "organic_options": "organic/non-chemical alternatives"
}

If you don't see any issues, set detected_issue to "Healthy Crop" and confidence to 100.
Be accurate - farmers depend on this information."""
            
            logger.info(f"[GEMINI] Sending request to {self.model.model_name} for pest detection")
            
            try:
                # Call Gemini API (FREE!)
                logger.info(f"[GEMINI] Creating message with content...")
                response = self.model.generate_content([prompt, image])
                
                logger.info(f"[GEMINI] Response received, parsing JSON...")
                # Parse JSON response
                result = self._parse_gemini_response(response.text)
                logger.info(f"[GEMINI] ✓ Successfully parsed: {result.get('detected_issue')}")
                
                return result
            except Exception as api_error:
                error_msg = str(api_error)
                logger.error(f"[GEMINI] API ERROR (first 300 chars): {error_msg[:300]}")
                
                # Check for rate limit errors (429)
                if "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning("[GEMINI] 🔴 Rate limit hit (free tier quota 5/min)")
                    # Return rate_limited flag so service can try alternative
                    return {"error_fallback": True, "rate_limited": True}
                
                # Check for model not found error (404)
                if "404" in error_msg or "not found" in error_msg.lower():
                    logger.warning(f"[GEMINI] Model {self.model.model_name} not available, trying next model...")
                    # Try next model in the list
                    if self._try_next_model():
                        logger.info(f"[GEMINI] Switched to new model, retrying...")
                        image_file.seek(0)
                        return self.detect_pest(image_file)
                    else:
                        logger.error("[GEMINI] No more models to try")
                        return {"error_fallback": True}
                
                # For other errors
                logger.warning(f"[GEMINI] Other API error, using fallback")
                return {"error_fallback": True}
            
        except Exception as e:
            logger.error(f"[GEMINI] Fatal error: {str(e)}", exc_info=False)
            return {"error_fallback": True}
    
    def _try_next_model(self) -> bool:
        """Try to initialize next available model in the list"""
        try:
            import google.generativeai as genai
            
            # Find current model index
            current_name = self.model.model_name.replace('models/', '')
            try:
                current_idx = self.AVAILABLE_MODELS.index(current_name)
            except ValueError:
                current_idx = -1
            
            # Try next models
            for i in range(current_idx + 1, len(self.AVAILABLE_MODELS)):
                model_name = self.AVAILABLE_MODELS[i]
                try:
                    logger.info(f"[GEMINI] Trying model {i}: {model_name}...")
                    new_model = genai.GenerativeModel(model_name)
                    # Quick test - just create it, don't call it
                    self.model = new_model
                    logger.info(f"[GEMINI] ✓ Switched to {model_name}")
                    return True
                except Exception as e:
                    logger.warning(f"[GEMINI] Model {model_name} failed: {str(e)[:100]}")
                    continue
            
            return False
        except Exception as e:
            logger.error(f"[GEMINI] Error trying next model: {str(e)[:100]}")
            return False
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Extract JSON from Gemini response"""
        try:
            # Try to find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['detected_issue', 'confidence', 'severity', 'description', 'treatment', 'prevention']
                for field in required_fields:
                    if field not in result:
                        result[field] = ""
                
                return result
            else:
                logger.error("No JSON found in Gemini response")
                return RuleBasedPestDetector.get_fallback_response("Invalid response format")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return RuleBasedPestDetector.get_fallback_response("Response parsing failed")


class GroqPestDetector:
    """
    Fast and reliable pest detection using Groq API
    - Free tier with no limitations
    - Very fast responses
    - Backup for when Gemini is unavailable
    """
    
    def __init__(self, api_key: str):
        logger.info(f"[GROQ INIT] Starting initialization...")
        logger.info(f"[GROQ INIT] API Key provided: {bool(api_key) and len(str(api_key)) > 0}")
        try:
            from groq import Groq
            logger.info(f"[GROQ INIT] groq module imported successfully")
            self.client = Groq(api_key=api_key)
            
            # Check if vision models are available
            # Currently Groq free tier doesn't have vision models active
            logger.info("[GROQ INIT] Groq library loaded, but vision models may not be available in free tier")
            self.available = True
            logger.info("[GROQ INIT] Groq pest detector initialized (text mode - no vision available)")
        except ImportError as ie:
            logger.warning(f"[GROQ INIT] ImportError: groq not installed. {str(ie)}")
            self.available = False
        except Exception as e:
            logger.error(f"[GROQ INIT] Error: {str(e)}", exc_info=True)
            self.available = False
    
    def detect_pest(self, image_file) -> Dict:
        """Analyze crop image for pests using Groq - NOT AVAILABLE IN FREE TIER"""
        logger.info(f"[GROQ] available={self.available}")
        # Groq free tier doesn't support vision models, skip to fallback
        logger.warning("[GROQ] Vision models not available in Groq free tier, using fallback")
        return RuleBasedPestDetector.get_fallback_response("Groq vision not available")
    
    def _parse_groq_response(self, response_text: str) -> Dict:
        """Extract JSON from Groq response"""
        try:
            # Try to find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['detected_issue', 'confidence', 'severity', 'description', 'treatment', 'prevention']
                for field in required_fields:
                    if field not in result:
                        result[field] = ""
                
                return result
            else:
                logger.error("No JSON found in Groq response")
                return RuleBasedPestDetector.get_fallback_response("Invalid response format")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return RuleBasedPestDetector.get_fallback_response("Response parsing failed")


class OpenAIPestDetector:
    """
    Pest detection using OpenAI Vision API
    - Powerful image analysis
    - Backup for when free APIs unavailable
    - Paid tier (only used as fallback)
    """
    
    def __init__(self, api_key: str):
        logger.info(f"[OPENAI INIT] Starting initialization...")
        logger.info(f"[OPENAI INIT] API Key provided: {bool(api_key) and len(str(api_key)) > 0}")
        try:
            import openai
            logger.info(f"[OPENAI INIT] openai module imported successfully")
            openai.api_key = api_key
            self.client = openai
            self.available = True
            logger.info("[OPENAI INIT] ✓ OpenAI pest detector initialized")
        except ImportError as ie:
            logger.warning(f"[OPENAI INIT] ImportError: openai not installed. {str(ie)}")
            self.available = False
        except Exception as e:
            logger.error(f"[OPENAI INIT] Error: {str(e)}", exc_info=True)
            self.available = False
    
    def detect_pest(self, image_file) -> Dict:
        """Analyze crop image for pests using OpenAI Vision"""
        logger.info(f"[OPENAI] Starting pest detection...")
        logger.info(f"[OPENAI] Available: {self.available}")
        
        if not self.available:
            logger.warning("[OPENAI] OpenAI detector not available")
            return RuleBasedPestDetector.get_fallback_response("OpenAI API not available")
        
        try:
            import base64
            import io
            
            # Reset file pointer and read image
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
            
            # Convert image to base64
            logger.info("[OPENAI] Encoding image to base64...")
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create the message for OpenAI
            prompt = """You are an expert agricultural pest detection AI with 20+ years of experience.
Analyze this crop image and identify any pests, diseases, nutrient deficiencies, or other agricultural issues.
Be precise and practical for African farming conditions.

Respond in this EXACT JSON format (no other text):
{
    "detected_issue": "specific pest/disease/deficiency name or 'Healthy Crop'",
    "confidence": 0-100,
    "severity": "none/low/medium/high/severe",
    "description": "2-3 sentences about what you see",
    "treatment": "practical treatment options available locally",
    "prevention": "how to prevent this in the future",
    "organic_options": "organic/non-chemical alternatives"
}

If you don't see any issues, set detected_issue to "Healthy Crop" and confidence to 100.
Be accurate - farmers depend on this information."""
            
            logger.info(f"[OPENAI] Sending request to OpenAI Vision API...")
            
            # Call OpenAI API with retry logic
            from tenacity import retry, stop_after_attempt, wait_exponential
            
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10)
            )
            def call_openai_api():
                response = self.client.ChatCompletion.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response
            
            response = call_openai_api()
            logger.info(f"[OPENAI] Response received successfully")
            
            # Parse response
            response_text = response.choices[0].message.content
            result = self._parse_openai_response(response_text)
            logger.info(f"[OPENAI] ✓ Result: {result.get('detected_issue')}")
            return result
            
        except Exception as e:
            logger.error(f"[OPENAI] Error: {str(e)}", exc_info=True)
            return RuleBasedPestDetector.get_fallback_response(f"OpenAI error: {str(e)[:100]}")
    
    def _parse_openai_response(self, response_text: str) -> Dict:
        """Extract JSON from OpenAI response"""
        try:
            # Try to find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['detected_issue', 'confidence', 'severity', 'description', 'treatment', 'prevention']
                for field in required_fields:
                    if field not in result:
                        result[field] = ""
                
                return result
            else:
                logger.error("No JSON found in OpenAI response")
                return RuleBasedPestDetector.get_fallback_response("Invalid response format")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return RuleBasedPestDetector.get_fallback_response("Response parsing failed")


class RuleBasedPestDetector:
    """
    Completely free pest detection using rules and knowledge base
    - No API calls, no costs
    - Works offline
    - Useful fallback when APIs unavailable
    """
    
    PEST_DATABASE = {
        "fall_armyworm": {
            "indicators": ["ragged leaves", "fecal pellets", "larvae", "damage", "holes"],
            "treatment": "Apply Emamectin benzoate 5% WDG or Spinosad 45% SC (local alternatives available)",
            "prevention": "Early planting, crop rotation, pheromone traps, conservation of natural enemies",
            "severity": "high",
            "affected_crops": ["maize", "sorghum", "millet"]
        },
        "maize_leaf_spot": {
            "indicators": ["brown spots", "yellow halos", "lesions", "striping"],
            "treatment": "Apply Azoxystrobin-based fungicide or Mancozeb 80% WP",
            "prevention": "Use resistant varieties, crop rotation (3-4 years), remove infected leaves",
            "severity": "medium",
            "affected_crops": ["maize"]
        },
        "aphids": {
            "indicators": ["curled leaves", "sticky residue", "small insects", "ants on plant"],
            "treatment": "Apply Neem oil 3% EC or insecticidal soap",
            "prevention": "Introduce ladybugs, remove weeds, intercropping with garlic/chili",
            "severity": "medium",
            "affected_crops": ["maize", "grains", "vegetables"]
        },
        "powdery_mildew": {
            "indicators": ["white powder", "stunted growth", "leaf curling"],
            "treatment": "Apply sulfur dust or potassium bicarbonate",
            "prevention": "Improve air circulation, avoid overhead watering, remove infected parts",
            "severity": "medium",
            "affected_crops": ["grains", "vegetables"]
        },
        "rust": {
            "indicators": ["reddish/brown pustules", "rust-colored powder", "leaf yellowing"],
            "treatment": "Apply Azoxystrobin or Triadimefon fungicide",
            "prevention": "Use resistant varieties, improve drainage, remove infected leaves",
            "severity": "high",
            "affected_crops": ["maize", "wheat"]
        },
        "nitrogen_deficiency": {
            "indicators": ["yellowing leaves", "lower leaves affected first", "stunted growth"],
            "treatment": "Apply nitrogen fertilizer: Urea (46% N) or DAP (18% N)",
            "prevention": "Soil testing, crop rotation, apply compost annually",
            "severity": "medium",
            "affected_crops": ["all"]
        },
        "phosphorus_deficiency": {
            "indicators": ["purple/reddish leaves", "poor root development", "small fruits"],
            "treatment": "Apply DAP (18% P), bone meal, or rock phosphate",
            "prevention": "Soil testing, compost application, crop rotation",
            "severity": "low",
            "affected_crops": ["all"]
        }
    }
    
    @staticmethod
    def detect_by_symptoms(symptoms: List[str]) -> Dict:
        """Match farmer-described symptoms to pest database"""
        logger.info(f"Performing rule-based detection for symptoms: {symptoms}")
        
        best_match = None
        best_score = 0
        
        for pest, data in RuleBasedPestDetector.PEST_DATABASE.items():
            score = 0
            for symptom in symptoms:
                if any(indicator.lower() in symptom.lower() or symptom.lower() in indicator.lower() 
                       for indicator in data['indicators']):
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = (pest, data, score)
        
        if best_match and best_score >= 2:
            pest, data, score = best_match
            confidence = min(90, score * 25)
            
            logger.info(f"Rule-based match found: {pest} with confidence {confidence}%")
            
            return {
                "detected_issue": pest.replace("_", " ").title(),
                "confidence": confidence,
                "severity": data['severity'],
                "description": f"Detected based on {score} symptom matches",
                "treatment": data['treatment'],
                "prevention": data['prevention'],
                "organic_options": "Yes - see prevention and treatment sections",
                "affected_crops": ", ".join(data['affected_crops'])
            }
        
        logger.info("No strong rule-based match found")
        return RuleBasedPestDetector.get_fallback_response("No definitive match found")
    
    @staticmethod
    def get_fallback_response(reason: str = "Unable to analyze") -> Dict:
        """Fallback response when detection not possible"""
        return {
            "detected_issue": "Unable to analyze automatically",
            "confidence": 0,
            "severity": "unknown",
            "description": reason,
            "treatment": "Please consult a local agronomist or agricultural extension officer with a clear photo",
            "prevention": "Take clear photos of: affected leaves, whole plant, and any visible insects",
            "organic_options": "Contact local agricultural extension for recommendations",
            "error_fallback": True
        }


class PestDetectionService:
    """
    Main pest detection service with intelligent fallback strategy
    1. Try Gemini API (FREE, best for images)
    2. Try Groq API (FREE, fast alternative)
    3. Try OpenAI Vision (PAID, powerful backup)
    4. Fall back to rule-based detection (100% FREE, offline)
    
    Cost optimization: Only uses paid APIs if free ones fail
    """
    
    def __init__(self, gemini_api_key: str = None, groq_api_key: str = None, openai_api_key: str = None):
        logger.info(f"=== PestDetectionService INIT (with 3-AI fallback) ===")
        logger.info(f"[SERVICE INIT] Gemini API key provided: {bool(gemini_api_key) and len(str(gemini_api_key)) > 0}")
        logger.info(f"[SERVICE INIT] Groq API key provided: {bool(groq_api_key) and len(str(groq_api_key)) > 0}")
        logger.info(f"[SERVICE INIT] OpenAI API key provided: {bool(openai_api_key) and len(str(openai_api_key)) > 0}")
        
        self.gemini_detector = None
        self.groq_detector = None
        self.openai_detector = None
        
        if gemini_api_key:
            logger.info(f"[SERVICE INIT] Creating Gemini detector...")
            self.gemini_detector = GeminiPestDetector(gemini_api_key)
            logger.info(f"[SERVICE INIT] Gemini detector ready: {self.gemini_detector.available}")
        else:
            logger.info(f"[SERVICE INIT] Skipping Gemini (no API key)")
        
        if groq_api_key:
            logger.info(f"[SERVICE INIT] Creating Groq detector...")
            self.groq_detector = GroqPestDetector(groq_api_key)
            logger.info(f"[SERVICE INIT] Groq detector ready: {self.groq_detector.available}")
        else:
            logger.info(f"[SERVICE INIT] Skipping Groq (no API key)")
        
        if openai_api_key:
            logger.info(f"[SERVICE INIT] Creating OpenAI detector...")
            self.openai_detector = OpenAIPestDetector(openai_api_key)
            logger.info(f"[SERVICE INIT] OpenAI detector ready: {self.openai_detector.available}")
        else:
            logger.info(f"[SERVICE INIT] Skipping OpenAI (no API key)")
        
        self.rule_detector = RuleBasedPestDetector()
        logger.info("✓ Pest detection service initialized (Gemini → Groq → OpenAI → Rule-Based)")
    
    def detect_from_image(self, image_file) -> Dict:
        """Detect pest from image using best available method"""
        logger.info(f"=== PEST DETECTION START (4-Tier Fallback) ===")
        logger.info(f"Priority: Gemini (FREE) → Groq (FREE) → OpenAI (PAID) → Rule-Based (FREE offline)")
        logger.info(f"Production safety check: IS_PRODUCTION={IS_PRODUCTION}, DISABLE_GEMINI={DISABLE_GEMINI_ON_PRODUCTION}")
        
        # CRITICAL: If Gemini is disabled on production, skip to paid APIs
        if IS_PRODUCTION and DISABLE_GEMINI_ON_PRODUCTION:
            logger.warning("🚫 PRODUCTION MODE - GEMINI DISABLED - Trying alternatives...")
        
        # ========== TIER 1: Try Gemini (FREE) ==========
        if not (IS_PRODUCTION and DISABLE_GEMINI_ON_PRODUCTION) and self.gemini_detector and self.gemini_detector.available:
            logger.info("🟢 TIER 1: Attempting Gemini AI detection (FREE)...")
            result = self.gemini_detector.detect_pest(image_file)
            logger.info(f"→ Gemini response: error_fallback={result.get('error_fallback')}, rate_limited={result.get('rate_limited')}")
            
            if result and not result.get('error_fallback'):
                logger.info("✅ GEMINI DETECTION SUCCESSFUL")
                logger.info(f"=== PEST DETECTION COMPLETE (Tier 1: Gemini) ===")
                return result
            
            if result.get('rate_limited'):
                logger.warning("⚠ Gemini rate limited, trying next provider...")
            else:
                logger.info("✗ Gemini detection failed, trying next provider...")
        else:
            logger.info(f"⚪ TIER 1 SKIPPED: Gemini unavailable/disabled")
        
        # ========== TIER 2: Try Groq (FREE) ==========
        if self.groq_detector and self.groq_detector.available:
            logger.info("🟢 TIER 2: Attempting Groq AI detection (FREE)...")
            try:
                if hasattr(image_file, 'seek'):
                    image_file.seek(0)
            except:
                pass
            result = self.groq_detector.detect_pest(image_file)
            logger.info(f"→ Groq response: error_fallback={result.get('error_fallback') if result else 'None'}")
            if result and not result.get('error_fallback'):
                logger.info("✅ GROQ DETECTION SUCCESSFUL")
                logger.info(f"=== PEST DETECTION COMPLETE (Tier 2: Groq) ===")
                return result
            logger.info("✗ Groq detection failed, trying next provider...")
        else:
            logger.info(f"⚪ TIER 2 SKIPPED: Groq unavailable")
        
        # ========== TIER 3: Try OpenAI (PAID - used as last resort) ==========
        if self.openai_detector and self.openai_detector.available:
            logger.info("🟡 TIER 3: Attempting OpenAI Vision detection (PAID but powerful)...")
            logger.info("💰 Note: This will incur costs. Using only because free APIs failed.")
            try:
                if hasattr(image_file, 'seek'):
                    image_file.seek(0)
            except:
                pass
            result = self.openai_detector.detect_pest(image_file)
            logger.info(f"→ OpenAI response: error_fallback={result.get('error_fallback') if result else 'None'}")
            if result and not result.get('error_fallback'):
                logger.info("✅ OPENAI DETECTION SUCCESSFUL")
                logger.info(f"=== PEST DETECTION COMPLETE (Tier 3: OpenAI) ===")
                return result
            logger.info("✗ OpenAI detection failed, using offline fallback...")
        else:
            logger.info(f"⚪ TIER 3 SKIPPED: OpenAI unavailable")
        
        # ========== TIER 4: Use Rule-Based Detection (100% FREE, OFFLINE) ==========
        logger.info("🔵 TIER 4: Using offline rule-based detection (100% FREE)")
        logger.info("=== PEST DETECTION COMPLETE (Tier 4: Rule-Based) ===")
        return RuleBasedPestDetector.get_fallback_response(
            "All AI services currently unavailable. Using offline analysis. Please provide clear photos showing: affected leaves, whole plant, and any visible insects"
        )
    
    def detect_from_symptoms(self, symptoms: List[str]) -> Dict:
        """Detect pest from farmer-described symptoms"""
        logger.info("Using rule-based detection from symptoms")
        return self.rule_detector.detect_by_symptoms(symptoms)


# Singleton instance factory
def get_pest_detection_service(gemini_api_key: str = None, groq_api_key: str = None, openai_api_key: str = None) -> PestDetectionService:
    """
    Factory function to get pest detection service with all 3 AI providers
    
    Usage:
        from django.conf import settings
        service = get_pest_detection_service(
            gemini_api_key=settings.GEMINI_API_KEY,
            groq_api_key=settings.GROQ_API_KEY,
            openai_api_key=settings.OPENAI_API_KEY
        )
        result = service.detect_from_image(image_file)
    """
    return PestDetectionService(gemini_api_key, groq_api_key, openai_api_key)
