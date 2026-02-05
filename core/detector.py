import os
import google.generativeai as genai
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a model appropriate for hackathon (fast)
model = genai.GenerativeModel('gemini-2.5-flash')

SCAM_KEYWORDS = [
    "account blocked", "kyc pending", "click this link", "verify immediately", 
    "urgent", "send otp", "share upi", "lottery", "winner", "prize", 
    "bank account suspended", "debit card blocked",
    # Indian context keywords
    "aadhar", "pan card", "rbi", "paytm", "phonepe", "gpay", 
    "light bill", "electricity connection", "challan"
]

def check_rules(text: str) -> Tuple[bool, float, str]:
    """
    Returns (is_scam, initial_confidence, reason)
    """
    text_lower = text.lower()
    for keyword in SCAM_KEYWORDS:
        if keyword in text_lower:
            return True, 0.85, f"Keyword match: {keyword}"
    
    return False, 0.0, "No keywords found"

async def classify_with_ai(text: str) -> Tuple[bool, float, str]:
    """
    Uses Gemini to classify scam.
    Returns (is_scam, confidence, reasoning)
    """
    try:
        prompt = f"""
        You are an Indian Scam Detection Expert. output JSON only.
        Analyze this message for scam probability, especially looking for common Indian scams (UPI, KYC, Electricity Bill, Job Offer).
        
        Message: '{text}'
        
        Output format:
        {{
            "is_scam": boolean, 
            "confidence": float (0.0-1.0), 
            "reason": string
        }}
        """
        print(f"\n[DEBUG] DETECTOR PROMPT:\n{prompt}\n")
        response = await model.generate_content_async(prompt)
        
        import json
        # Extract JSON from response (Gemini might add markdown backticks)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw_text)
        
        return result.get("is_scam", False), result.get("confidence", 0.0), result.get("reason", "AI analysis")
    except Exception as e:
        print(f"AI Classification Error: {e}")
        # Fallback to rule-based or neutral
        return False, 0.0, "AI Error"
