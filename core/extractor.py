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
    """
    Uses Gemini AI to extract intelligence from the conversation text.
    Capable of identifying obfuscated payment details and nuanced red flags.
    
    Args:
        text (str): The conversation history or message text to analyze.
        
    Returns:
        ExtractedIntelligence: A structured object containing extracted data.
    """
    try:
        prompt = f"""
        Extract scam intelligence from this message. Output JSON only.
        
        Message: '{text}'
        
        Extract:
        - phoneNumbers: Indian mobile numbers (e.g., +91..., 98...)
        - bankAccounts: Any bank account numbers
        - upiIds: UPI IDs (e.g., name@bank)
        - phishingLinks: Suspicious URLs
        - suspiciousKeywords: Identify key red flags, urgency tactics, or requests for sensitive info (e.g., "PAN", "Aadhar", "OTP", "urgent", "blocked", "KYC", "police", "arrest", "suspend").
        - emailAddresses: Any email addresses mentioned
        - caseIds: Any case numbers, reference IDs, or file numbers mentioned
        - policyNumbers: Any insurance policy numbers mentioned
        - orderNumbers: Any order or tracking numbers mentioned
        
        If nothing found for a category, use empty list [].
        
        Output format:
        {{
            "phoneNumbers": [],
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "suspiciousKeywords": [],
            "emailAddresses": [],
            "caseIds": [],
            "policyNumbers": [],
            "orderNumbers": []
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
            suspiciousKeywords=data.get("suspiciousKeywords", []),
            emailAddresses=data.get("emailAddresses", []),
            caseIds=data.get("caseIds", []),
            policyNumbers=data.get("policyNumbers", []),
            orderNumbers=data.get("orderNumbers", [])
        )
    except Exception as e:
        print(f"AI Extraction Error: {e}")
        return ExtractedIntelligence()

async def extract_all(text: str) -> ExtractedIntelligence:
    """
    Combines regex-based fast extraction with AI-based deep extraction to 
    maximize the recall of scam-related intelligence (UPI, Links, Bank Accounts, Phones, Keywords).
    
    Args:
        text (str): The conversation history or message text to analyze.
        
    Returns:
        ExtractedIntelligence: A merged object containing all unique extracted items.
    """
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
    data.suspiciousKeywords = list(set(data.suspiciousKeywords + ai_data.suspiciousKeywords))
    data.emailAddresses = list(set(data.emailAddresses + ai_data.emailAddresses))
    data.caseIds = list(set(data.caseIds + ai_data.caseIds))
    data.policyNumbers = list(set(data.policyNumbers + ai_data.policyNumbers))
    data.orderNumbers = list(set(data.orderNumbers + ai_data.orderNumbers))

    return data

