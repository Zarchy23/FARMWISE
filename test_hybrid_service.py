#!/usr/bin/env python3
"""
Test Hybrid Prediction Service
Tests the combination of local models and external AI APIs
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.services.hybrid_prediction_service import hybrid_service
import tempfile
import json

def test_hybrid_yield():
    """Test hybrid yield prediction"""
    print("=" * 60)
    print("Testing Hybrid Yield Prediction")
    print("=" * 60)
    
    features = {
        'area_hectares': 5.0,
        'soil_nitrogen': 45,
        'soil_phosphorus': 78,
        'soil_potassium': 50,
        'soil_ph': 6.5,
        'temperature_avg': 23,
        'rainfall_mm': 650,
        'humidity': 65,
        'fertilizer_kg_ha': 100,
        'irrigation_days': 10,
        'pesticide_used': 5,
        'disease_severity': 2
    }
    
    try:
        result = hybrid_service.predict_yield_hybrid(features, use_api_fallback=False)
        print("Result:", json.dumps(result, indent=2))
        print("✅ Yield prediction test passed")
    except Exception as e:
        print(f"❌ Yield prediction test failed: {e}")
    print()

def test_hybrid_pest():
    """Test hybrid pest prediction"""
    print("=" * 60)
    print("Testing Hybrid Pest Prediction")
    print("=" * 60)
    
    # Create a dummy test image
    try:
        from PIL import Image
        import numpy as np
        
        # Create a simple test image
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp, format='JPEG')
            tmp_path = tmp.name
        
        try:
            result = hybrid_service.predict_pest_hybrid(tmp_path, use_api_fallback=False)
            print("Result:", json.dumps(result, indent=2))
            print("✅ Pest prediction test passed")
        except Exception as e:
            print(f"❌ Pest prediction test failed: {e}")
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        print(f"❌ Could not create test image: {e}")
    print()

def test_hybrid_disease():
    """Test hybrid disease prediction"""
    print("=" * 60)
    print("Testing Hybrid Disease Prediction")
    print("=" * 60)
    
    # Create a dummy test image
    try:
        from PIL import Image
        import numpy as np
        
        # Create a simple test image
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp, format='JPEG')
            tmp_path = tmp.name
        
        try:
            result = hybrid_service.predict_disease_hybrid(tmp_path, use_api_fallback=False)
            print("Result:", json.dumps(result, indent=2))
            print("✅ Disease prediction test passed")
        except Exception as e:
            print(f"❌ Disease prediction test failed: {e}")
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        print(f"❌ Could not create test image: {e}")
    print()

if __name__ == "__main__":
    print("Hybrid Prediction Service Test Suite")
    print("=" * 60)
    print()
    
    test_hybrid_yield()
    test_hybrid_pest()
    test_hybrid_disease()
    
    print("=" * 60)
    print("Test Suite Complete")
    print("=" * 60)
