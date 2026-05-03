# DocTome — Medical Credential Verification Platform

DocTome is an AI-powered platform that automatically verifies the credentials of medical practitioners (doctors, clinics, and laboratories). It uses a multi-agent LangGraph pipeline on the backend and a modern React frontend.

---

## Features

- Supports three entity types: **Doctor**, **Clinic**, **Laboratory**
- Accepts PDF, JPG, and PNG documents (diplomas, licenses, ISO certificates, etc.)
- 3-agent AI pipeline: extraction → verification → decision report
- Trust score (0–100) with decision: `APPROVED`, `PENDING_REVIEW`, or `REJECTED`
- PDF report generation and email delivery via SendGrid
- Dark/light theme UI

---

## Project Structure

```
hackathon/
├── frontend/                  # React + Vite frontend
│   └── src/
│       ├── components/        # UI components
│       ├── context/           # Theme context
│       ├── App.jsx            # Main app + routing
│       └── main.jsx
│
└── doctome_langgraph/         # FastAPI backend + LangGraph pipeline
    ├── main.py                # FastAPI app & /api/verify endpoint
    ├── graph.py               # LangGraph workflow definition
    ├── agents/
    │   ├── agent1_extraction.py      # Agent 1: Document extraction
    │   ├── agent2.py                 # Agent 2: Credential verification
    │   ├── agent3.py                 # Agent 3: Report & decision
    │   ├── state.py                  # Shared PractitionerState schema
    │   ├── prompts.py                # LLM prompt templates
    │   ├── verification_pipeline.py  # Structural scoring rules
    │   ├── qr_verifier.py            # QR code extraction
    │   └── schemas/                  # Gold-standard JSON schemas
    ├── data/                  # Sample test documents
    ├── output/                # Generated reports (JSON + PDF)
    └── .env                   # API keys (Groq, Google, SendGrid)
```

---

## Tech Stack

| Layer     | Technology |
|-----------|-----------|
| Frontend  | React 19, Vite, Tailwind CSS, Framer Motion |
| Backend   | Python, FastAPI, Uvicorn |
| AI / LLM  | LangGraph, Groq (Llama 3.1) |
| OCR       | pdfplumber, EasyOCR, pytesseract |
| Email     | SendGrid REST API |
| Reports   | fpdf2 (PDF generation) |

---

## Getting Started

### 1. Backend

```bash
cd doctome_langgraph
pip install -r requirements.txt   # install dependencies
```

Create a `.env` file (or use the existing one):
```
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
SENDGRID_API_KEY=your_sendgrid_key
```

Start the API server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** (or the port shown in the terminal).

---

## API

### `POST /api/verify`

Accepts `multipart/form-data`:

| Field | Type | Description |
|-------|------|-------------|
| `doctorName` | string | Full name or entity name |
| `licenseNumber` | string | License / registration number |
| `specialty` | string | Medical specialty or facility type |
| `country` | string | Country of practice |
| `entityType` | string | `doctor`, `clinic`, or `lab` |
| `files` | file[] | Document files (PDF / JPG / PNG) |

Returns a JSON object with trust score, decision, issues, and pipeline details.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for Llama 3.1 LLM calls |
| `GOOGLE_API_KEY` | Google API key (Vision / Gemini) |
| `SENDGRID_API_KEY` | SendGrid key for email delivery |
| `VITE_API_URL` | (Frontend) Backend URL, default `http://localhost:8000` |
