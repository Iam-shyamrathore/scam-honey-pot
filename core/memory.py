from typing import List, Dict, Any

# Global in-memory storage for hackathon speed
# Structure: {session_id: {"callback_sent": bool}}
SESSION_META: Dict[str, Dict[str, Any]] = {}

def get_history_mock(session_id: str) -> List[Dict[str, str]]:
    # In the new problem statement, history is PASSED in the request.
    # So we don't strictly need to store it, but we might want to store metadata.
    return []

def mark_callback_sent(session_id: str):
    if session_id not in SESSION_META:
        SESSION_META[session_id] = {}
    SESSION_META[session_id]["callback_sent"] = True

def is_callback_sent(session_id: str) -> bool:
    return SESSION_META.get(session_id, {}).get("callback_sent", False)
