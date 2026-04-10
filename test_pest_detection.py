#!/usr/bin/env python
"""
Test pest detection with real uploaded image
This ensures the Gemini API is working end-to-end
"""
import os
import sys
import django
import logging
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

# Import after Django setup
from django.conf import settings
from core.services.pest_detection import PestDetectionService

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get API keys from settings
GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', None)

logger.info(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")
logger.info(f"GROQ_API_KEY present: {bool(GROQ_API_KEY)}")

# Find a test image
test_image_path = 'media/pest_detection/2026/04/gettyimages-1396936527-612x612.jpg'

if not os.path.exists(test_image_path):
    logger.error(f"❌ Test image not found: {test_image_path}")
    sys.exit(1)

logger.info(f"✓ Test image found: {test_image_path}")

# Open image and test pest detection
try:
    with open(test_image_path, 'rb') as image_file:
        logger.info("\n" + "="*60)
        logger.info("TESTING PEST DETECTION SERVICE")
        logger.info("="*60)
        
        pest_service = PestDetectionService(GEMINI_API_KEY, GROQ_API_KEY)
        result = pest_service.detect_from_image(image_file)
        
        logger.info("\n" + "="*60)
        logger.info("RESULT:")
        logger.info("="*60)
        logger.info(f"Detected Issue: {result.get('detected_issue')}")
        logger.info(f"Confidence: {result.get('confidence')}%")
        logger.info(f"Severity: {result.get('severity')}")
        logger.info(f"Description: {result.get('description')}")
        logger.info(f"Treatment: {result.get('treatment')}")
        logger.info(f"Prevention: {result.get('prevention')}")
        logger.info(f"Organic Options: {result.get('organic_options')}")
        logger.info(f"Error Fallback: {result.get('error_fallback')}")
        logger.info("="*60)
        
        # Show success or failure
        if result.get('error_fallback'):
            logger.warning("⚠️  FALLBACK RESPONSE - AI analysis not successful")
        else:
            logger.info("✅ REAL AI ANALYSIS - Pest detection working!")
        
except Exception as e:
    logger.error(f"❌ Test failed: {e}", exc_info=True)
    sys.exit(1)
