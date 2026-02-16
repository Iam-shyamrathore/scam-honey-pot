from models.schemas import ExtractedIntelligence

# Global in-memory storage for hackathon speed
# Structure: {session_id: {"last_intel_count": int, "msg_count": int}}
SESSION_META: Dict[str, Dict[str, Any]] = {}

def get_total_intel_count(intel: ExtractedIntelligence) -> int:
    return (
        len(intel.upiIds) + 
        len(intel.phoneNumbers) + 
        len(intel.bankAccounts) + 
        len(intel.phishingLinks)
    )

def should_update_callback(session_id: str, new_intel: ExtractedIntelligence, msg_count: int) -> bool:
    """
    Returns True if:
    1. First time sending callback
    2. New intelligence found (count increased)
    3. Significantly more messages (e.g. every 5 messages) - optional, but good for liveness
    """
    if session_id not in SESSION_META:
        SESSION_META[session_id] = {"last_intel_count": 0, "last_msg_count": 0}
        
    meta = SESSION_META[session_id]
    current_intel_count = get_total_intel_count(new_intel)
    
    # Trigger if new intel found
    if current_intel_count > meta["last_intel_count"]:
        return True
        
    # Trigger if conversation is getting long and we haven't updated in a while (e.g. +5 msgs)
    # This ensures we send *some* update even if no new intel, just to show engagement
    if msg_count >= meta["last_msg_count"] + 5:
        return True
        
    return False

def mark_callback_sent(session_id: str, intel: ExtractedIntelligence, msg_count: int):
    if session_id not in SESSION_META:
        SESSION_META[session_id] = {}
    
    SESSION_META[session_id]["last_intel_count"] = get_total_intel_count(intel)
    SESSION_META[session_id]["last_msg_count"] = msg_count

