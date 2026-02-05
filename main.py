from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import os

# Import our custom modules
from models.schemas import ScamEvent, AgentResponse, FinalResultPayload
from core.detector import check_rules, classify_with_ai
from core.engagement import select_persona, generate_reply, PERSONAS
from core.extractor import extract_all
from core.memory import is_callback_sent, mark_callback_sent
from core.callback import send_final_result

# Load environment variables
load_dotenv()

app = FastAPI(title="Agentic Honey-Pot Scam Detector (Guvi Edition)")

API_KEY = os.getenv("API_KEY", "HACKATHON_SECRET_KEY")

@app.post("/detect-scam", response_model=AgentResponse)
async def detect_scam(
    event: ScamEvent, 
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None)
):
    # 1. Official Auth: x-api-key header
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    # 2. Extract Message
    user_msg_text = event.message.text
    session_id = event.sessionId
    
    # 3. Scam Detection
    # Hybrid Check
    is_scam, confidence, reason = check_rules(user_msg_text)
    if not is_scam:
        # If no keywords, check AI
        is_scam, confidence, reason = await classify_with_ai(user_msg_text)

    # 4. Intelligence Extraction
    # We extract from the LATEST message AND potential history if needed.
    # For optimization, we just scan current text.
    intelligence = extract_all(user_msg_text)

    # 5. Agentic Engagement
    if is_scam:
        # Reconstruct History format for Engagement Module
        # Engagement module expects list of dicts: {'role': 'user'/'assistant', 'content': '...'}
        # The incoming `event.conversationHistory` has `sender`='scammer'/'user'.
        # We need to map: 'scammer' -> 'user' (for our AI model), 'user' -> 'assistant' (our past replies)
        # Wait, the problem statement says:
        # sender: "scammer" -> The bad guy.
        # sender: "user" -> Wait, is "user" the victim (us)?
        # 6.2 Example shows: 
        # History: [{sender: "scammer", text: "..."}, {sender: "user", text: "Why will my account be blocked?"}]
        # So "user" in history is OUR AI (The HoneyPot).
        
        formatted_history = []
        for msg in event.conversationHistory:
            role = "user" if msg.sender == "scammer" else "assistant"
            formatted_history.append({"role": role, "content": msg.text})
            
        # Pick a persona. Ideally sticky per session.
        # We'll use a deterministic hash of session_id to pick consistent persona
        import hashlib
        persona_keys = list(PERSONAS.keys())
        hash_idx = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % len(persona_keys)
        persona_key = persona_keys[hash_idx]
        
        reply_text = await generate_reply(formatted_history, persona_key, user_msg_text)
        
        # 6. Callback Check
        # Trigger if: Scam Detected AND (Intelligence Found OR Long Conversation) AND Not Sent
        has_intelligence = (
            intelligence.bankAccounts or 
            intelligence.upiIds or 
            intelligence.phishingLinks or 
            intelligence.phoneNumbers
        )
        msg_count = len(event.conversationHistory) + 1
        
        # Debug Logs for User Visibility
        print(f"\n[DEBUG] Extracted Intel: {intelligence.model_dump()}")
        print(f"[DEBUG] Msg Count: {msg_count}")
        print(f"[DEBUG] Has Intelligence: {has_intelligence}")
        
        if not is_callback_sent(session_id):
            if has_intelligence or msg_count > 5:
                # Prepare Payload
                # Note: We should ideally aggregate intelligence from WHOLE history.
                # For hackathon, we send what we found NOW. 
                # Improvement: Persist extracted intel to send aggregate.
                # Let's simple send what we found in this turn + default empty.
                
                final_payload = FinalResultPayload(
                    sessionId=session_id,
                    scamDetected=True,
                    totalMessagesExchanged=msg_count,
                    extractedIntelligence=intelligence,
                    agentNotes=f"Detected via {reason}. Persona used: {persona_key}."
                )
                
                # Send in background to not block response
                background_tasks.add_task(send_final_result, final_payload)
                mark_callback_sent(session_id)
            else:
                print(f"[DEBUG] Callback SKIPPED: Needs Intelligence OR >5 messages (Current: {msg_count})")
        else:
            print(f"[DEBUG] Callback SKIPPED: Already Sent for Session {session_id}")
                
    else:
        # Not a scam
        reply_text = "Hello, how can I help you?"

    # 7. Response
    return AgentResponse(
        status="success",
        reply=reply_text
    )

if __name__ == "__main__":
    import uvicorn
    # Use PORT env var if available (DigitalOcean), else 8001
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
