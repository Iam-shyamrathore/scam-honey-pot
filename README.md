# Agentic Honey-Pot Scam Detector

An advanced, AI-first honeypot API designed to detect, engage, and extract intelligence from scammers in real-time. Built with FastAPI and powered by Google's Gemini 2.5 Flash, this system acts as a proactive defense mechanism against phishing, UPI fraud, and KYC scams.

## 🌟 Key Features

*   **AI-First Detection**: Moves beyond simple keyword matching. Gemini analyzes the full context of messages to identify sophisticated scams (urgency tactics, unsolicited requests).
*   **Proactive Engagement**: Uses dynamic, Indian-context personas (e.g., "Desi Uncle", "Confused Student") to keep scammers engaged. The bot actively probes for payment details and verification links to maximize intelligence gathering.
*   **Hybrid Intelligence Extraction**: Combines fast, precise Regex patterns with deep AI extraction. Capable of identifying obfuscated UPI IDs, Bank Accounts, Phishing Links, and nuanced Red Flags (`suspiciousKeywords`).
*   **Smart Callbacks**: Aggregates intelligence across multi-turn conversations. If a scammer reveals new details (e.g., a bank account in turn 5 after giving a UPI in turn 2), the system automatically fires an updated callback webhook.

## 🚀 Getting Started

### Prerequisites

*   Python 3.9+
*   A Gemini API Key (from Google AI Studio)
*   (Optional) A Guvi Callback Webhook URL for reporting

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Iam-shyamrathore/scam-honey-pot.git
    cd scam-honey-pot
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up your Environment Variables. Create a `.env` file in the root directory:
    ```env
    API_KEY=your_secret_api_key_for_auth
    GEMINI_API_KEY=your_gemini_api_key
    GUVI_WEBHOOK_URL=https://hackathon.guvi.in/api/webhook # Optional
    PORT=8001
    ```

### Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --port 8001 --reload
```
The API will be available at `http://localhost:8001`.

## 🧪 Testing

The repository includes a comprehensive test suite that simulates real-world scam scenarios (Bank Fraud, UPI Fraud, Phishing, and multi-turn KYC probing).

To run the tests, ensure your server is running, then execute:
```bash
python3 test_scenarios.py
```

## 📚 Documentation
For detailed information on the system architecture, API endpoints, and the intelligence extraction logic, please see the `docs/` directory.

- [API Reference](docs/API_REFERENCE.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
