from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# --- Shared Models (Must be defined first) ---

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    suspiciousKeywords: List[str] = []
    emailAddresses: List[str] = []
    caseIds: List[str] = []
    policyNumbers: List[str] = []
    orderNumbers: List[str] = []

# --- Input Models ---

class Message(BaseModel):
    sender: str  # "scammer" or "user"
    text: str
    timestamp: Optional[int] = None

class Metadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class ScamEvent(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None

# --- Output Models ---

class AgentResponse(BaseModel):
    status: str = "success"
    reply: str
    
    # The evaluation system's parser might fail if we return extra data here.
    # We must only return exactly what is specified in Section 4: Expected API Response Format.

# --- Callback Models ---

class FinalResultPayload(BaseModel):
    sessionId: str
    scamDetected: bool
    totalMessagesExchanged: int
    engagementDurationSeconds: int
    extractedIntelligence: ExtractedIntelligence
    agentNotes: str
