# IntentGuard: Zero-Trust LLM E-Commerce

IntentGuard is an advanced AI architecture that safely connects Large Language Models to real-world transactions without hallucinations.

## Features
- **Deterministic Verification Engine**: Prevents LLM hallucination in pricing and details.
- **Universal Commerce Protocol (UCP)**: A unified abstraction for handling e-commerce, telecom, and utility payments.
- **Live Google Shopping & Web API**: Dynamically fetches the exact real-time prices and valid products.
- **Zero-Trust Slot Filling**: Securely parses PII and critical transaction constraints.

## Tech Stack
- Frontend: React + Vite
- Backend: Python + FastAPI + SQLAlchemy + SQLite
- Integrations: Groq (Llama 3), Serper API (Google Shopping / DuckDuckGo)

## Setup
### Backend
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

### Frontend
```bash
npm install
npm run dev
```
