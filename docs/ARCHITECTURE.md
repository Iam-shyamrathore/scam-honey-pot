# Architecture Overview

The Agentic Honey-Pot Scam Detector is built on a modular, asynchronous architecture using FastAPI and Google Gemini. The system is designed to be highly concurrent, processing multiple I/O-bound requests efficiently without blocking.

## Core Modules

The application logic is broken down into distinct modules located in the `core/` directory:

### 1. `detector.py` (Scam Detection)
*   **Role**: Determines if an incoming message is a scam.
*   **Approach**: Uses an AI-First strategy. While traditional keywords are still tracked, every message is passed to `classify_with_ai` (Gemini 2.5 Flash).
*   **Prompting**: The AI is instructed with specific rules regarding Indian scams (UPI fraud, KYC, Electricity Bills) and urgency tactics, allowing it to understand the nuance of a message rather than just looking for trigger words.

### 2. `extractor.py` (Intelligence Extraction)
*   **Role**: Pulls actionable data from the conversation.
*   **Approach**: Hybrid Extraction.
    *   **Regex Engine**: First, fast regular expressions scan the text for standard patterns (UPI IDs, URLs, Indian mobile numbers).
    *   **AI Engine**: Next, the full conversation history is passed to `extract_with_ai`. The AI acts as a deep scanner, capable of finding obfuscated numbers and identifying specific `suspiciousKeywords` (Red Flags like "arrest", "PAN block", "urgent").
*   **Aggregation**: The results from both engines are merged (union) to ensure maximum recall.

### 3. `engagement.py` (Persona Generation)
*   **Role**: Generates realistic replies to waste the scammer's time and gather more information.
*   **Approach**: Persona-driven. Based on a hash of the `sessionId`, a consistent persona (e.g., "Desi Uncle", "Corporate Employee") is selected.
*   **Probing Strategy**: The AI prompt includes a `CRITICAL STRATEGY` section. If the scammer hasn't provided payment details, the bot is instructed to play dumb and actively request a UPI ID or Bank Account. For KYC scams, it asks for official apps or verification links.

### 4. `memory.py` (State Management)
*   **Role**: Tracks the state of ongoing sessions.
*   **Approach**: Given the hackathon constraints, state is maintained in a global, in-memory dictionary (`SESSION_META`). 
*   **Smart Updates**: It tracks the total count of extracted intelligence per session. This powers the "Smart Callback" feature, ensuring that we only trigger external webhooks when new information is discovered or after significant conversational progress.

## Flow Diagram

1.  **Incoming Request** (`POST /detect-scam`) -> Auth Check
2.  **Detection** -> `classify_with_ai` (Is it a scam?)
3.  **Extraction** -> `extract_all(history + current_message)` (Pull UPIs, Links, Red Flags)
4.  **Engagement** (If Scam) -> `generate_reply` (Ask probing questions based on Persona)
5.  **Memory / Callback** -> `should_update_callback` (Has intelligence count increased?) -> Trigger `send_final_result` as Background Task.
6.  **Response** -> Return `AgentResponse` to client.
