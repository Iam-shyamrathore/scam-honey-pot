import httpx
from models.schemas import FinalResultPayload

CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

async def send_final_result(payload: FinalResultPayload):
    """
    Sends the final extracted intelligence to the evaluation endpoint.
    This is best effort (fire and forget pattern or logged).
    """
    try:
        data = payload.model_dump()
        import json
        print(f"\n[DEBUG] CALLBACK PAYLOAD TO GUVI:\n{json.dumps(data, indent=2)}\n")
        async with httpx.AsyncClient() as client:
            response = await client.post(CALLBACK_URL, json=data, timeout=5.0)
            if response.status_code == 200:
                print(f"Callback SUCCESS for {payload.sessionId}")
            else:
                print(f"Callback FAILED for {payload.sessionId}: {response.text}")
    except Exception as e:
        print(f"Callback ERROR for {payload.sessionId}: {e}")
