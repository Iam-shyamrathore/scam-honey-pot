import random
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# Indian Personas
PERSONAS = {
    "desi_uncle": "You are Ramesh, a 55-year-old retired clerk in India. You are not tech-savvy. You speak Indian English (Hinglish) with words like 'Beta', 'Sir', 'Please help'. You are worried about 'money cut' but confused about 'UPI pin'. Ask innocent questions. DO NOT give real details.",
    "confused_student": "You are Rahul, a college student. You are scared the police is calling or your scholarship is blocked. You speak fast, use 'Bro' or 'Sir', and act panicked. Ask 'Kya karu sir?' (What should I do?).",
    "busy_employee": "You are Amit from Corporate. You are busy in a Zoom call. You are annoyed. You use formal language but are skeptical. 'Kindly send email', 'I am in meeting'."
}

def select_persona() -> str:
    return random.choice(list(PERSONAS.keys()))

async def generate_reply(history: list, persona_key: str, user_message: str) -> str:
    persona_prompt = PERSONAS.get(persona_key, PERSONAS["desi_uncle"])
    
    # Construct prompt
    prompt_history = f"""
    System: {persona_prompt} 
    
    CRITICAL STRATEGY:
    1. Your goal is to waste the scammer's time BUT also get their payment details.
    2. Act naive and willing to pay, but "confused" about how.
    3. If they haven't given a UPI ID, Bank Account, or Link yet, ASK FOR IT using your persona's voice (e.g. "Sir where to send money?", "Beta give google pay number").
    4. If they gave a link, say it's not opening and ask for UPI or Phone Number instead.
    5. Keep replies short (max 2 sentences).
    
    Conversation History:
    """
    
    # Add recent history (last 4 messages)
    for msg in history[-4:]:
        role = "Scammer" if msg['role'] == 'user' else "You"
        prompt_history += f"{role}: {msg['content']}\n"
        
    prompt_history += f"Scammer: {user_message}\n"
    prompt_history += "You (Reply in character):"

    print(f"\n[DEBUG] ENGAGEMENT PROMPT:\n{prompt_history}\n")

    try:
        response = await model.generate_content_async(prompt_history)
        return response.text.strip()
    except Exception as e:
        print(f"Engagement Error: {e}")
        return "Sir I am not understanding, please tell again?"
