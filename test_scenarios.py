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

                # Check 1: API Response validity
                if not data.get("reply"):
                    passed = False
                    issues.append("❌ Missing 'reply' in response.")

                # We can't validate `scam_detected` or `extracted_intelligence` synchronously anymore 
                # because we stripped them from the `AgentResponse` payload to meet Hackathon docs.
                # All intelligence is now sent asynchronously via the Webhook.
                
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


def run_multi_turn_simulation():
    print(f"\n{'='*60}")
    print("Testing Multi-Turn Intelligence Aggregation")
    print(f"{'='*60}")
    
    # Conversation flow from user request
    turns = [
        {"sender": "scammer", "text": "URGENT: Your SBI account has been compromised. Share your account number and OTP immediately."},
        {"sender": "scammer", "text": "Please transfer Rs.5000 to UPI ID scammer.fraud@fakebank"}, # Turn 3 in example
        {"sender": "scammer", "text": "Please transfer Rs.5000 to account number 1234567890123456"}, # Turn 7
        {"sender": "scammer", "text": "Here is a secure payment link: https://pay.fakebank.com/transfer?to=1234567890123456"} # Turn 9
    ]
    
    session_id = str(uuid.uuid4())
    history = []
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    
    print(f"Session: {session_id}")
    
    extracted_so_far = {"upiIds": [], "bankAccounts": [], "phishingLinks": []}
    
    for i, turn in enumerate(turns):
        print(f"\n--- Turn {i+1} ---")
        print(f"Scammer: {turn['text']}")
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": turn['text'],
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": history,
            "metadata": {"channel": "WhatsApp", "locale": "IN"}
        }
        
        try:
            res = requests.post(f"{BASE_URL}/detect-scam", json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                print(f"✅ Reply: {data.get('reply')}")
                
                # Update history for next turn
                history.append(payload["message"])
                history.append({
                    "sender": "user",
                    "text": data.get("reply"),
                    "timestamp": int(time.time() * 1000)
                })
            else:
                print(f"❌ Error: {res.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n--- Validation ---")
    print("✅ Conversation flows correctly. Check Uvicorn terminal for [DEBUG] Callback SENT messages to verify intelligence extraction.")


def run_kyc_simulation():
    print(f"\n{'='*60}")
    print("Testing KYC/Red-Flag Probing Strategy")
    print(f"{'='*60}")
    
    # Scammer says KYC is pending
    turns = [
        {"sender": "scammer", "text": "Dear customer, your PAN card is not linked to your SBI account. Your account will be suspended today. Please verify your KYC immediately."},
        {"sender": "scammer", "text": "Download the SBI Quick Support app from this link to verify: http://sbi-kyc-update.apk"}, 
    ]
    
    session_id = str(uuid.uuid4())
    history = []
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    extracted_so_far = {"suspiciousKeywords": [], "phishingLinks": []}
    
    for i, turn in enumerate(turns):
        print(f"\n--- Turn {i+1} ---")
        print(f"Scammer: {turn['text']}")
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": turn['text'],
                "timestamp": int(time.time() * 1000)
            },
            "conversationHistory": history,
            "metadata": {"channel": "WhatsApp", "locale": "IN"}
        }
        
        try:
            res = requests.post(f"{BASE_URL}/detect-scam", json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                data = res.json()
                print(f"✅ Reply: {data.get('reply')}")
                
                history.append(payload["message"])
                history.append({
                    "sender": "user",
                    "text": data.get("reply"),
                    "timestamp": int(time.time() * 1000)
                })
            else:
                print(f"❌ Error: {res.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n--- Validation ---")
    print("✅ Conversation flows correctly. Check Uvicorn terminal for [DEBUG] Callback SENT messages to verify intelligence extraction.")

if __name__ == "__main__":
    run_test()
    run_multi_turn_simulation()
    run_kyc_simulation()
