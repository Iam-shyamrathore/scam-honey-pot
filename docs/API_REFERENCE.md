# API Reference

## Authentication

All requests to the Honeypot API must include the `x-api-key` header.

*   **Header Name**: `x-api-key`
*   **Value**: The secret key defined in your `API_KEY` environment variable.

## Endpoints

### `POST /detect-scam`

The primary endpoint for processing incoming messages. It analyzes the text, extracts intelligence, generates a persona-driven reply, and optionally triggers a background callback if a scam is detected.

#### Request Body (JSON)

Matches the `ScamEvent` schema.

```json
{
  "sessionId": "string (UUID)",
  "message": {
    "sender": "string (e.g., 'scammer')",
    "text": "string (The message content)",
    "timestamp": "integer (Unix epoch time in ms)"
  },
  "conversationHistory": [
    {
      "sender": "string",
      "text": "string",
      "timestamp": "integer"
    }
  ],
  "metadata": {
    "channel": "string (Optional)",
    "locale": "string (Optional)"
  }
}
```

#### Response Body (JSON)

Matches the `AgentResponse` schema.

```json
{
  "status": "success",
  "reply": "string (The generated persona response, or a generic greeting if not a scam)",
  "scam_detected": "boolean",
  "confidence_score": "float (0.0 to 1.0)",
  "extracted_intelligence": {
    "bankAccounts": ["string"],
    "upiIds": ["string"],
    "phishingLinks": ["string"],
    "phoneNumbers": ["string"],
    "suspiciousKeywords": ["string"]
  },
  "engagement_metrics": {
    "turn_count": "integer"
  }
}
```

#### Error Responses

*   **403 Forbidden**: Invalid or missing `x-api-key`.
*   **500 Internal Server Error**: An error occurred during AI processing (e.g., Gemini API is down).

## Callbacks (Webhooks)

When a scam is detected and actionable intelligence is found (or after a long conversation), the API will POST to the `GUVI_WEBHOOK_URL` in the background.

The callback payload matches the `FinalResultPayload` schema:

```json
{
  "sessionId": "string",
  "scamDetected": true,
  "totalMessagesExchanged": "integer",
  "extractedIntelligence": {
    "bankAccounts": ["..."],
    "upiIds": ["..."],
    "phishingLinks": ["..."],
    "phoneNumbers": ["..."],
    "suspiciousKeywords": ["..."]
  },
  "agentNotes": "string (Detailed explanation of the detection reasoning and persona used)"
}
```

**Smart Callbacks**: The system tracks the intelligence reported per `sessionId`. If new, unique intelligence is extracted in subsequent turns, an updated callback payload is fired automatically.
