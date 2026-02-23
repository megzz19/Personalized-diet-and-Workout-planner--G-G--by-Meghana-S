from fastapi.testclient import TestClient
from main import app
import json


def test_generate_plan(client):
    print("="*50)
    print("TEST 1: Valid Plan Generation")
    print("="*50)
    payload = {
        "age": 25,
        "height": 175,
        "weight": 70,
        "gender": "male",
        "foodType": "Non-Veg",
        "activityLevel": "moderately_active",
        "goal": "muscle_gain"
    }
    response = client.post("/generate-plan", json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Structure Keys:", list(data.keys()))
        print(f"Diet Recommendations: {len(data['diet_plan'])} items")
        print(f"Workout Recommendations: {len(data['workout_plan'])} items")
        print("Daily Stats:", data['daily_stats'])
        print("Tips:", data['additional_tips'])
    else:
        print("Error:", response.text)

def test_invalid_input(client):
    print("\n" + "="*50)
    print("TEST 2: Invalid Input Validation")
    print("="*50)
    # Test strict validation (Age < 10)
    payload = {
        "age": 5, # Invalid
        "height": 175,
        "weight": 70,
        "gender": "male",
        "foodType": "Veg",
        "activityLevel": "sedentary",
        "goal": "health"
    }
    response = client.post("/generate-plan", json=payload)
    print(f"Status Code: {response.status_code} (Expected 422)")
    if response.status_code == 422:
        print("Validation Error Correctly Raised.")
    else:
        print("Validation Failed to trigger!")

def test_sanitization(client):
    print("\n" + "="*50)
    print("TEST 3: XSS Sanitization")
    print("="*50)
    # Test XSS
    payload = {
        "age": 25, "height": 175, "weight": 70, "gender": "male", 
        "foodType": "Veg", "activityLevel": "sedentary",
        "goal": "<script>alert('HACKED')</script>Weight Loss"
    }
    # It should pass validation but sanitizer should strip script?
    response = client.post("/generate-plan", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("Sanitization seemed to process without crashing.")

if __name__ == "__main__":
    with TestClient(app) as client:
        test_generate_plan(client)
        test_invalid_input(client)
        test_sanitization(client)
