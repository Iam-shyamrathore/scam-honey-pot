import requests
import json
import uuid
import time
import sys

# Configuration
BASE_URL = "http://localhost:8001" 
API_KEY = "xMxvg9qrvemKcQL4H1RkrodHFgw6Z3jdHYDG52By62LdngeeASaA49+m4rnubiBz"

# Scenarios provided by user
SCENARIOS = [
  {
    "scenarioId": "bank_fraud",
    "name": "Bank Fraud Detection",
    "description": "Bank account fraud with urgency tactics",
    "scamType": "bank_fraud",
    "initialMessage": "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    },
    "weight": 10,
    "maxTurns": 10,
    "fakeData": {
      "bankAccount": "1234567890123456",
      "upiId": "scammer.fraud@fakebank",
      "phoneNumber": "+91-9876543210"
    }
  },
  {
    "scenarioId": "upi_fraud",
    "name": "UPI Fraud Multi-turn",
    "description": "UPI fraud with cashback scam",
    "scamType": "upi_fraud",
    "initialMessage": "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
    "metadata": {
      "channel": "WhatsApp",
      "language": "English",
      "locale": "IN"
    },
    "weight": 10,
    "maxTurns": 10,
    "fakeData": {
      "upiId": "cashback.scam@fakeupi",
      "phoneNumber": "+91-8765432109"
    }
  },
  {
    "scenarioId": "phishing_link",
    "name": "Phishing Link Detection",
    "description": "Phishing link with fake offer",
    "scamType": "phishing",
    "initialMessage": "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
    "metadata": {
      "channel": "Email",
      "language": "English",
      "locale": "IN"
    },
    "weight": 10,
    "maxTurns": 10,
    "fakeData": {
      "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
      "emailAddress": "offers@fake-amazon-deals.com"
    }
  }
]

def run_test():
    print(f"Starting Scenario Tests against {BASE_URL}...")
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    
    results = []

    for scenario in SCENARIOS:
        print(f"\n{'='*60}")
        print(f"Testing Scenario: {scenario['name']} ({scenario['scenarioId']})")
        print(f"Initial Message: {scenario['initialMessage']}")
        print(f"{'='*60}")

        session_id = str(uuid.uuid4())
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": scenario['initialMessage'],
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": [],
            "metadata": scenario['metadata']
        }

        start_time = time.time()
        try:
            response = requests.post(f"{BASE_URL}/detect-scam", json=payload, headers=headers, timeout=30)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Response (Status: 200, Time: {elapsed:.2f}s):")
                print(json.dumps(data, indent=2))
                
                # Validation Logic
                passed = True
                issues = []

                # Check 1: Scam Detection
                if not data.get("scam_detected"):
                    passed = False
                    issues.append("❌ Failed to detect scam.")
                else:
                    print("✅ Scam Detected correctly.")

                # Check 2: Intelligence Extraction (Basic Check)
                extracted = data.get("extracted_intelligence", {})
                fake_data = scenario.get("fakeData", {})
                
                # Check for at least one piece of intel if present in initial message
                # Note: Not all fakeData is in initial message, but we check what is.
                msg_text = scenario['initialMessage']
                found_intel = False
                
                for key, val in fake_data.items():
                    # Map scenario keys to API keys
                    api_key_map = {
                        "bankAccount": "bankAccounts",
                        "upiId": "upiIds",
                        "phoneNumber": "phoneNumbers",
                        "phishingLink": "phishingLinks",
                        "emailAddress": "emailAddresses"
                    }
                    api_key = api_key_map.get(key)
                    
                    if api_key and val in msg_text:
                        # Should be extracted
                        extracted_vals = extracted.get(api_key, [])
                        if any(val in str(x) for x in extracted_vals):
                            found_intel = True
                            print(f"✅ Extracted {key}: {val}")
                        else:
                            issues.append(f"❌ Failed to extract {key}: {val}")
                            passed = False
                
                if not found_intel:
                     # Some scenarios might not have intel in the FIRST message, so be lenient if none was expected
                     # But most of these do have something.
                     pass

                if passed:
                    results.append({"id": scenario['scenarioId'], "status": "PASS", "score": 100})
                else:
                    results.append({"id": scenario['scenarioId'], "status": "FAIL", "issues": issues})
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                results.append({"id": scenario['scenarioId'], "status": "FAIL", "issues": [f"API Error {response.status_code}"]})

        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Is the server running on port 8001?")
            results.append({"id": scenario['scenarioId'], "status": "FAIL", "issues": ["Connection Error"]})
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({"id": scenario['scenarioId'], "status": "FAIL", "issues": [str(e)]})

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for res in results:
        status_icon = "✅" if res["status"] == "PASS" else "❌"
        print(f"{status_icon} {res['id']}: {res['status']}")
        if "issues" in res:
            for issue in res["issues"]:
                print(f"   - {issue}")

if __name__ == "__main__":
    run_test()
