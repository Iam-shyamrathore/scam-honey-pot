import re
from typing import List
from models.schemas import ExtractedIntelligence


import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

async def extract_with_ai(text: str) -> ExtractedIntelligence:
    try:
        prompt = f"""
        Extract scam intelligence from this message. Output JSON only.
        
        Message: '{text}'
        
        Extract:
        - phoneNumbers: Indian mobile numbers (e.g., +91..., 98...)
        - bankAccounts: Any bank account numbers
        - upiIds: UPI IDs (e.g., name@bank)
        - phishingLinks: Suspicious URLs
        
        If nothing found for a category, use empty list [].
        
        Output format:
        {{
            "phoneNumbers": [],
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": []
        }}
        """
        response = await model.generate_content_async(prompt)
        import json
        raw = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        
        return ExtractedIntelligence(
            phoneNumbers=data.get("phoneNumbers", []),
            bankAccounts=data.get("bankAccounts", []),
            upiIds=data.get("upiIds", []),
            phishingLinks=data.get("phishingLinks", []),
            suspiciousKeywords=[]
        )
    except Exception as e:
        print(f"AI Extraction Error: {e}")
        return ExtractedIntelligence()

async def extract_all(text: str) -> ExtractedIntelligence:
    data = ExtractedIntelligence()
    
    # 1. Regex Extraction (Fast & Precise for standard patterns)
    # UPI Pattern
    upi_matches = re.findall(r"[a-zA-Z0-9.\-_]{3,}@[a-zA-Z]{3,}", text)
    data.upiIds = list(set(upi_matches))

    # URL Pattern
    url_matches = re.findall(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*", text)
    data.phishingLinks = list(set(url_matches))
        
    # Mobile Number
    mobile_matches = re.findall(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b", text)
    data.phoneNumbers = list(set(mobile_matches))
    
    # Bank Account
    if "account" in text.lower() or "ac" in text.lower() or "bank" in text.lower():
         acc_matches = re.findall(r"\b\d{9,18}\b", text)
         data.bankAccounts = list(set(acc_matches))

    # Keywords
    keywords = ["urgent", "verify now", "account blocked", "kyc", "suspend", "block", "electricity", "cut"]
    found_keywords = [k for k in keywords if k in text.lower()]
    data.suspiciousKeywords = list(set(found_keywords))
    
    # 2. AI Extraction (For tricky/obfuscated patterns)
    ai_data = await extract_with_ai(text)
    
    # Merge Results (Union)
    data.upiIds = list(set(data.upiIds + ai_data.upiIds))
    data.phishingLinks = list(set(data.phishingLinks + ai_data.phishingLinks))
    data.phoneNumbers = list(set(data.phoneNumbers + ai_data.phoneNumbers))
    data.bankAccounts = list(set(data.bankAccounts + ai_data.bankAccounts))

    return data

