import re
from typing import List
from models.schemas import ExtractedIntelligence

def extract_all(text: str) -> ExtractedIntelligence:
    data = ExtractedIntelligence()
    
    # UPI Pattern
    upi_matches = re.findall(r"[a-zA-Z0-9.\-_]{3,}@[a-zA-Z]{3,}", text)
    data.upiIds = list(set(upi_matches)) # Dedup

    # URL Pattern
    url_matches = re.findall(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*", text)
    data.phishingLinks = list(set(url_matches))
        
    # Indian Mobile Number (+91-XXXXX or 10 digits starting 6-9)
    # Using findall to get all numbers
    mobile_matches = re.findall(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b", text)
    data.phoneNumbers = list(set(mobile_matches))
    
    # Bank Account (9-18 digits) - simplified for hackathon
    # Only if context is present
    if "account" in text.lower() or "ac" in text.lower() or "bank" in text.lower():
         acc_matches = re.findall(r"\b\d{9,18}\b", text)
         # Filter out things that look like mobiles (10 digits starting with 6-9) from bank accounts logic if needed,
         # but for now, raw extraction is fine.
         data.bankAccounts = list(set(acc_matches))

    # Suspicious Keywords (Rule-based subset)
    keywords = ["urgent", "verify now", "account blocked", "kyc", "suspend", "block", "electricity", "cut"]
    found_keywords = [k for k in keywords if k in text.lower()]
    data.suspiciousKeywords = list(set(found_keywords))

    return data
