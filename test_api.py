import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_KEY = "HACKATHON_SECRET_KEY"

def test_scam_detection():
    print("Testing Scam Detection (Indian Context)...")
    payload = {
        "api_key": API_KEY,
        "message": "Dear Sir, your electricity connection will be cut tonight at 9 PM because your previous month bill was not updated. Please immediately contact our electricity officer 9890909090. Pay KYC"
    }
    
    start = time.time()
    try:
        response = requests.post(f"{BASE_URL}/detect-scam", json=payload)
        duration = time.time() - start
        
        print(f"Status: {response.status_code}")
        print(f"Time: {duration:.2f}s")
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_safe_message():
    print("\nTesting Safe Message...")
    payload = {
        "api_key": API_KEY,
        "message": "Hey mom, just checking in. How are you?"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/detect-scam", json=payload)
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Wait for server to start if running via script
    time.sleep(2) 
    test_scam_detection()
    test_safe_message()
