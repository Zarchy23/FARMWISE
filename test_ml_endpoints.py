#!/usr/bin/env python3
import requests
import json
import os

# Test ML API endpoints
base_url = "http://127.0.0.1:8000"

def test_model_status():
    """Test model status endpoint"""
    print("=" * 50)
    print("Testing Model Status")
    print("=" * 50)
    try:
        response = requests.get(f"{base_url}/ml/status/")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Model Status:", json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_yield_prediction():
    """Test yield prediction endpoint"""
    print("=" * 50)
    print("Testing Yield Prediction")
    print("=" * 50)
    features = {
        "area_hectares": 5.0,
        "soil_nitrogen": 45,
        "soil_phosphorus": 78,
        "soil_potassium": 50,
        "soil_ph": 6.5,
        "temperature_avg": 23,
        "rainfall_mm": 650,
        "humidity": 65,
        "fertilizer_kg_ha": 100,
        "irrigation_days": 10,
        "pesticide_used": 5,
        "disease_severity": 2
    }
    try:
        response = requests.post(f"{base_url}/ml/predict/yield/", json=features)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Yield Prediction:", json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_disease_prediction():
    """Test disease prediction endpoint"""
    print("=" * 50)
    print("Testing Disease Prediction")
    print("=" * 50)
    
    # Check if we have a test image
    test_image = "test_plant.jpg"
    if not os.path.exists(test_image):
        print(f"No test image found at {test_image}")
        print("Create a test image to test disease prediction")
        return
    
    try:
        with open(test_image, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{base_url}/ml/predict/disease/", files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Disease Prediction:", json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_pest_prediction():
    """Test pest prediction endpoint"""
    print("=" * 50)
    print("Testing Pest Prediction")
    print("=" * 50)
    
    # Check if we have a test image
    test_image = "test_pest.jpg"
    if not os.path.exists(test_image):
        print(f"No test image found at {test_image}")
        print("Create a test image to test pest prediction")
        return
    
    try:
        with open(test_image, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{base_url}/ml/predict/pest/", files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Pest Prediction:", json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    print("ML API Endpoint Tester")
    print("=" * 50)
    print()
    
    # Test all endpoints
    test_model_status()
    test_yield_prediction()
    test_disease_prediction()
    test_pest_prediction()
    
    print("=" * 50)
    print("Testing Complete")
    print("=" * 50)
