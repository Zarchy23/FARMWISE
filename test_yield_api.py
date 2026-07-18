#!/usr/bin/env python3
import requests
import json

# Test yield prediction API
status_url = "http://127.0.0.1:8000/ml/status/"
predict_url = "http://127.0.0.1:8000/ml/predict/yield/"

# Sample features
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
    # First check if server is running
    print("Checking server status...")
    response = requests.get(status_url)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("Model Status:", response.json())
        
        # Test yield prediction
        print("\nTesting yield prediction...")
        response = requests.post(predict_url, json=features)
        print(f"Predict Status Code: {response.status_code}")
        print(f"Predict Response: {response.text}")
        
        if response.status_code == 200:
            print("\nYield Prediction Result:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.status_code} - {response.text}")
    else:
        print(f"Server returned status code: {response.status_code}")
    
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to server. Make sure Django server is running at http://127.0.0.1:8000/")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
