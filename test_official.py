import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8001"
API_KEY = "AAAkE8gmGj+6pZtZsdiTviRoh3NJl+PX2fvss612yt4dx5vRRfVAQqRn0+ZhVtzI"

def test_official_flow():
    session_id = str(uuid.uuid4())
    print(f"\n--- Testing Official Flow (Session: {session_id}) ---")
    
    # 1. First Message (Scam Start)
    msg1 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Your electricity connection will be disconnected tonight. Call 9812345678 immediately.",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "locale": "IN"}
    }
    
    print("\n[Step 1] Sending First Scam Message...")
    start = time.time()
    try:
        res = requests.post(
            f"{BASE_URL}/detect-scam", 
            json=msg1, 
            headers={"x-api-key": API_KEY}
        )
        if res.status_code == 200:
            print("Response:", json.dumps(res.json(), indent=2))
            ai_reply_1 = res.json().get("reply")
        else:
            print(f"Error: {res.text}")
            ai_reply_1 = "System Error"
    except Exception as e:
        print(f"Failed: {e}")
        return

    # 2. Second Message (Scammer Follow-up)
    # Simulator: User (AI) replied, now Scammer replies again.
    # We construct history manually for the request
    history = [
        {"sender": "scammer", "text": msg1["message"]["text"]},
        {"sender": "user", "text": ai_reply_1} # "user" in history is our AI
    ]
    
    msg2 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Pay rs 10 to update KYC now.",
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": history,
        "metadata": {"channel": "SMS", "locale": "IN"}
    }
    
    print("\n[Step 2] Sending Follow-up Message...")
    start = time.time()
    try:
        res = requests.post(
            f"{BASE_URL}/detect-scam", 
            json=msg2, 
            headers={"x-api-key": API_KEY}
        )
        print(f"Status: {res.status_code}, Time: {time.time()-start:.2f}s")
        print("Response:", json.dumps(res.json(), indent=2))
    except Exception as e:
        print(f"Failed: {e}")

    print("\n[Check] Callback should have been triggered in background logic if intelligence was found.")

if __name__ == "__main__":
    time.sleep(2) # Wait for startup
    test_official_flow()
