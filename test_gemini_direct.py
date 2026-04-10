#!/usr/bin/env python
"""
Direct test of Gemini API for pest detection
This tests if the Google Generative AI library can communicate with API
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging 
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
logger.info(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")

if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not found in environment!")
    sys.exit(1)

try:
    import google.generativeai as genai
    logger.info("✓ google-generativeai library imported")
except ImportError as e:
    logger.error(f"❌ Failed to import google-generativeai: {e}")
    sys.exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
logger.info("✓ Gemini configured with API key")

# List available models
logger.info("\n📋 Listing available models...")
try:
    models = genai.list_models()
    for model in models:
        logger.info(f"  - {model.name}: {model.display_name}")
except Exception as e:
    logger.error(f"❌ Failed to list models: {e}")

# Test each model
models_to_test = [
    'gemini-2.0-flash-exp',
    'gemini-1.5-pro',
    'gemini-1.5-flash',
    'gemini-pro-vision',
    'gemini-pro',
]

logger.info("\n🧪 Testing models with generateContent()...")

# Create a simple test prompt (no image for now)
test_prompt = "Say 'Test successful' and confirm you received this message."

for model_name in models_to_test:
    logger.info(f"\n  Testing {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        logger.info(f"    ✓ Model initialized: {model_name}")
        
        # Try simple text generation first
        response = model.generate_content(test_prompt, stream=False)
        logger.info(f"    ✓ Text generation works: {response.text[:50]}...")
        
    except ValueError as ve:
        logger.warning(f"    ⚠ ValueError: {str(ve)[:100]}")
    except Exception as e:
        logger.warning(f"    ⚠ Error: {str(e)[:100]}")

# Now test with actual image if file exists
logger.info("\n🖼️  Testing with actual image...")
test_image_path = 'test_pest_image.jpg'
if os.path.exists(test_image_path):
    logger.info(f"  Found test image: {test_image_path}")
    
    from PIL import Image
    try:
        image = Image.open(test_image_path)
        logger.info(f"  ✓ Image loaded: {image.size}")
        
        # Test with gemini-1.5-flash (most likely to work)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            "This is an agricultural image. Describe what you see briefly.",
            image
        ])
        logger.info(f"  ✓ Vision test passed: {response.text[:100]}...")
        
    except Exception as e:
        logger.error(f"  ❌ Vision test failed: {e}", exc_info=True)
else:
    logger.warning(f"  ⚠ No test image found at {test_image_path}")

logger.info("\n✅ Gemini API test complete!")
