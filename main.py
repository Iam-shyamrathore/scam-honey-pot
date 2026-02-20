from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import os

# Import our custom modules
from models.schemas import ScamEvent, AgentResponse, FinalResultPayload
from core.detector import check_rules, classify_with_ai
from core.engagement import select_persona, generate_reply, PERSONAS
from core.extractor import extract_all
from core.memory import mark_callback_sent
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
    """
    Main webhook endpoint for the Scam Detection Honey-Pot.
    Processes incoming messages, identifies scams, extracts intelligence (UPI, Links, Bank Accounts, Keywords),
    and generates a persona-driven reply to engage the scammer.
    """
    # 1. Official Auth: x-api-key header
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    # 2. Extract Message
    user_msg_text = event.message.text
    session_id = event.sessionId
    
    try:
        # 3. Scam Detection
        # AI - First Approach (Full Intelligence)
        # check_rules is now just a fallback/signal, we primarily use AI
        is_scam, confidence, reason, scam_type = await classify_with_ai(user_msg_text)
    
        # 4. Intelligence Extraction
        # Optimization: Scan WHOLE history to catch details dropped in prev turns
        full_text = user_msg_text
        for prev_msg in event.conversationHistory:
            full_text += f" {prev_msg.text}"
            
        # Now async because it uses AI
        intelligence = await extract_all(full_text)
    except Exception as e:
        print(f"Error during AI Processing: {e}")
        # Log the error but try to gracefully fail or return a 500
        raise HTTPException(status_code=500, detail="Internal AI Error Processing Message")
        
    # Defaults in case not defined
    msg_count = len(event.conversationHistory) + 1

    # 5. Agentic Engagement
    if is_scam:
        # Reconstruct History format for Engagement Module
        
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
        # Trigger if: Scam Detected AND (New Intelligence Found OR Long Conversation Update)
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
        
        from core.memory import should_update_callback, mark_callback_sent
        
        # Check if we should send an update
        if should_update_callback(session_id, intelligence, msg_count):
             if has_intelligence:
                # Prepare Payload
                final_payload = FinalResultPayload(
                    sessionId=session_id,
                    scamDetected=True,
                    totalMessagesExchanged=msg_count,
                    extractedIntelligence=intelligence,
                    agentNotes=f"Detected via {reason}. Persona used: {persona_key}. SCAM TYPE: {scam_type}"
                )
                
                # Send in background to not block response
                background_tasks.add_task(send_final_result, final_payload)
                mark_callback_sent(session_id, intelligence, msg_count)
                print(f"[DEBUG] Callback SENT/UPDATED for Session {session_id}")
             else:
                print(f"[DEBUG] Callback SKIPPED: No intelligence found yet.")
        else:
             print(f"[DEBUG] Callback SKIPPED: No new info to report.")
                
    else:
        # Not a scam
        reply_text = "Hello, how can I help you?"

    # 7. Response
    # 7. Response
    return AgentResponse(
        status="success",
        reply=reply_text,
        scam_detected=is_scam,
        confidence_score=confidence,
        extracted_intelligence=intelligence,
        engagement_metrics={"turn_count": msg_count}
    )

if __name__ == "__main__":
    import uvicorn
    # Use PORT env var if available (DigitalOcean), else 8001
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
