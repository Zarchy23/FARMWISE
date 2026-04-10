#!/usr/bin/env python
"""
Test pest detection with a fresh start and rate limit handling
"""
import os
import sys
import time
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.conf import settings
from core.services.pest_detection import PestDetectionService

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)
GROQ_API_KEY = getattr(settings, 'GROQ_API_KEY', None)

test_image_path = 'media/pest_detection/2026/04/istockphoto-483451251-612x612.jpg'

if not os.path.exists(test_image_path):
    logger.error(f"❌ Test image not found: {test_image_path}")
    sys.exit(1)

logger.info(f"✓ Test image: {test_image_path}")
logger.info("\n" + "="*70)
logger.info("TESTING REAL PEST DETECTION WITH GEMINI AI")
logger.info("="*70 + "\n")

try:
    with open(test_image_path, 'rb') as image_file:
        pest_service = PestDetectionService(GEMINI_API_KEY, GROQ_API_KEY)
        result = pest_service.detect_from_image(image_file)
        
        logger.info("\n" + "="*70)
        logger.info("PEST DETECTION RESULT:")
        logger.info("="*70)
        
        if result.get('error_fallback'):
            if result.get('rate_limited'):
                logger.warning("⚠️  RATE LIMITED - Free tier quota hit (5 req/min)")
                logger.info("   ➜ Will automatically try Groq or rule-based fallback")
            else:
                logger.warning("⚠️  FALLBACK RESPONSE")
        else:
            logger.info("✅ REAL AI ANALYSIS SUCCESSFUL!")
        
        logger.info(f"\nDetected Issue: {result.get('detected_issue')}")
        logger.info(f"Confidence: {result.get('confidence')}%")
        logger.info(f"Severity: {result.get('severity')}")
        logger.info(f"Description:\n  {result.get('description')}")
        logger.info(f"\nTreatment:\n  {result.get('treatment')}")
        logger.info(f"\nPrevention:\n  {result.get('prevention')}")
        logger.info(f"\nOrganic Options:\n  {result.get('organic_options')}")
        logger.info("="*70)
        
except Exception as e:
    logger.error(f"❌ Test failed: {e}", exc_info=True)
    sys.exit(1)
