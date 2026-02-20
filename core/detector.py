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
    "account blocked", "kyc pending", "click this link", "click here", "verify immediately", 
    "urgent", "send otp", "share upi", "lottery", "winner", "prize", "claim", "offer",
    "selected for", "iphone", "rs.",
    "bank account suspended", "debit card blocked",
    # Indian context keywords
    "aadhar", "pan card", "rbi", "paytm", "phonepe", "gpay", 
    "light bill", "electricity connection", "challan"
]


def check_rules(text: str) -> Tuple[bool, float, str]:
    """
    Legacy rule-based check for initial scam detection.
    Currently acts as a passthrough to force the more intelligent AI classification.
    
    Args:
        text (str): The current message text.
        
    Returns:
        Tuple[bool, float, str]: (is_scam, initial_confidence, reason)
    """
    return False, 0.0, "Proceed to AI Check"

async def classify_with_ai(text: str) -> Tuple[bool, float, str, str]:
    """
    Uses Gemini AI to perform deep contextual classification of a potential scam message.
    It identifies nuances like urgency, unsolicited requests, and specific Indian scam types.
    
    Args:
        text (str): The user/scammer message to classify.
        
    Returns:
        Tuple[bool, float, str, str]: (is_scam, confidence_score, reasoning_explanation, scam_type)
    """
    try:
        prompt = f"""
        You are an Indian Scam Detection Expert. Output JSON only.
        Analyze this message for scam probability.
        
        Message: '{text}'
        
        Context & Rules:
        1. Context: User is receiving this message (SMS/WhatsApp/Email).
        2. Indian Scams: Look for UPI fraud, KYC pending, Electricity Bill cut, Job Offers, Lottery, Fake Rewards/iPhone.
        3. Phishing: Suspicious links (bit.ly, fake domains) are 100% scam.
        4. Urgency: 'Immediately', 'Within 2 hours', 'Account blocked' are strong indicators.
        5. Unsolicited: If it asks for money/OTP/personal info out of nowhere, it is a scam.
        
        Output format:
        {{
            "is_scam": boolean, 
            "confidence": float (0.0-1.0), 
            "reason": "Brief explanation",
            "scam_type": "Bank Fraud" | "UPI Fraud" | "Phishing" | "Job Scam" | "Other" | "None"
        }}
        """
        # print(f"\n[DEBUG] DETECTOR PROMPT:\n{prompt}\n")
        response = await model.generate_content_async(prompt)
        
        import json
        # Extract JSON from response (Gemini might add markdown backticks)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw_text)
        
        return (
            result.get("is_scam", False), 
            result.get("confidence", 0.0), 
            result.get("reason", "AI analysis"),
            result.get("scam_type", "None")
        )
    except Exception as e:
        print(f"AI Classification Error: {e}")
        # Fallback to keyword check if AI fails
        text_lower = text.lower()
        for keyword in SCAM_KEYWORDS:
             if keyword in text_lower:
                 return True, 0.85, f"Keyword match (Fallback): {keyword}", "Unknown"
        return False, 0.0, "AI Error", "None"

