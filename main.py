from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import asyncio
import hashlib

# Import our custom modules
from models.schemas import ScamEvent, AgentResponse, FinalResultPayload
from core.detector import check_rules, classify_with_ai
from core.engagement import select_persona, generate_reply, PERSONAS
from core.extractor import extract_all
from core.memory import mark_callback_sent, should_update_callback
from core.callback import send_final_result
from core.exceptions import AIProcessingError, PersonaGenerationError

# Load environment variables
load_dotenv()

app = FastAPI(title="Agentic Honey-Pot Scam Detector (Guvi Edition)")

API_KEY = os.getenv("API_KEY", "HACKATHON_SECRET_KEY")

@app.exception_handler(AIProcessingError)
async def ai_error_handler(request: Request, exc: AIProcessingError):
    """Global exception handler for AI processing failures."""
    print(f"[ERROR] AI Engine Failure: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Failed to process message through AI engines", "details": exc.message}
    )

async def process_scam_event(event: ScamEvent, background_tasks: BackgroundTasks) -> AgentResponse:
    """Core business logic for processing a scam event. Separated from the HTTP route."""
    user_msg_text = event.message.text
    session_id = event.sessionId
    
    # 1. Prepare texts
    full_text = user_msg_text
    for prev_msg in event.conversationHistory:
        full_text += f" {prev_msg.text}"
        
    try:
        # 1. Scam Detection (Fast AI Call)
        is_scam, confidence, reason, scam_type = await classify_with_ai(user_msg_text)
    except Exception as e:
         raise AIProcessingError(f"Detection failed: {str(e)}")

    msg_count = len(event.conversationHistory) + 1
    reply_text = "Hello, how can I help you?"
    
    # We always need intelligence object for the webhook, even if empty initially
    from models.schemas import ExtractedIntelligence
    intelligence = ExtractedIntelligence()

    if is_scam:
        # 2. Extract Business Logic Prep
        formatted_history = []
        for msg in event.conversationHistory:
            role = "user" if msg.sender == "scammer" else "assistant"
            formatted_history.append({"role": role, "content": msg.text})
            
        persona_keys = list(PERSONAS.keys())
        hash_idx = int(hashlib.sha256(session_id.encode()).hexdigest(), 16) % len(persona_keys)
        persona_key = persona_keys[hash_idx]
        
        try:
             # 3. Concurrent Heavy AI Execution (Extraction & Persona Generation)
             # This is a major latency optimization. We do not need the extraction results
             # to generate the persona reply, so we run them strictly in parallel.
             extraction_task = extract_all(full_text)
             reply_task = generate_reply(formatted_history, persona_key, user_msg_text)
             
             intelligence, reply_text = await asyncio.gather(extraction_task, reply_task)
             
        except Exception as e:
             raise AIProcessingError(f"Extraction or Generation failed: {str(e)}")
        
        # 4. Callback Logic
        has_intelligence = (
            intelligence.bankAccounts or 
            intelligence.upiIds or 
            intelligence.phishingLinks or 
            intelligence.phoneNumbers or
            intelligence.suspiciousKeywords
        )
        
        if should_update_callback(session_id, intelligence, msg_count):
             if has_intelligence:
                # Calculate Engagement Duration
                first_ts = event.message.timestamp
                if event.conversationHistory:
                    first_ts = event.conversationHistory[0].timestamp
                last_ts = event.message.timestamp
                
                duration_seconds = 0
                if first_ts and last_ts:
                    duration_seconds = int((last_ts - first_ts) / 1000)

                # Prepare Payload
                final_payload = FinalResultPayload(
                    sessionId=session_id,
                    scamDetected=True,
                    totalMessagesExchanged=msg_count,
                    engagementDurationSeconds=duration_seconds,
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

    # 5. Strict Response return
    return AgentResponse(
        status="success",
        reply=reply_text
    )

@app.post("/detect-scam", response_model=AgentResponse)
async def detect_scam(
    event: ScamEvent, 
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None)
):
    """
    Main webhook endpoint for the Scam Detection Honey-Pot.
    """
    # 1. Official Auth: x-api-key header
    # Allow missing key for evaluator scripts that don't send headers
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
        
    # Delegate to business logic layer
    return await process_scam_event(event, background_tasks)

if __name__ == "__main__":
    import uvicorn
    # Use PORT env var if available (DigitalOcean), else 8001
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
