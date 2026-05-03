# DocTome — Architecture Overview

## High-Level Architecture

```
User (Browser)
     │
     │  multipart/form-data (name, license, files)
     ▼
┌─────────────────────────────┐
│     React Frontend          │
│  (Vite + Tailwind CSS)      │
│                             │
│  LandingPage → UploadForm   │
│  → PipelineStatus           │
│  → ResultsDashboard         │
└──────────────┬──────────────┘
               │ POST /api/verify
               ▼
┌─────────────────────────────┐
│     FastAPI Backend         │
│       (main.py)             │
│                             │
│  - Saves uploaded files     │
│  - Detects document types   │
│  - Calls LangGraph workflow │
│  - Returns structured JSON  │
└──────────────┬──────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│           LangGraph Pipeline                 │
│              (graph.py)                      │
│                                              │
│  START                                       │
│    │                                         │
│    ▼                                         │
│  ┌──────────────────────────────────────┐    │
│  │  Agent 1 — Document Extraction       │    │
│  │  agent1_extraction.py                │    │
│  │                                      │    │
│  │  • PDF text extraction (pdfplumber)  │    │
│  │  • Image OCR (EasyOCR / Tesseract)   │    │
│  │  • LLM structuring (Groq Llama 3.1)  │    │
│  │  • Quality score per document        │    │
│  │  • Anomaly detection                 │    │
│  └────────────────┬─────────────────────┘    │
│                   │ extraction_json_output   │
│                   ▼                          │
│  ┌──────────────────────────────────────┐    │
│  │  Agent 2 — Credential Verification   │    │
│  │  agent2.py                           │    │
│  │                                      │    │
│  │  • Structural score: extracted JSON  │    │
│  │    vs gold-standard schemas          │    │
│  │  • Semantic score: LLM content check │    │
│  │  • QR code verification              │    │
│  │  • Trust score = (struct + sem) / 2  │    │
│  │  • Flags suspicious credentials      │    │
│  └────────────────┬─────────────────────┘    │
│                   │ trust_score,             │
│                   │ credential_flags         │
│                   ▼                          │
│  ┌──────────────────────────────────────┐    │
│  │  Agent 3 — Report & Decision         │    │
│  │  agent3.py                           │    │
│  │                                      │    │
│  │  • Groq LLM decision reasoning       │    │
│  │  • Score > 85  → APPROVED            │    │
│  │  • Score 50–85 → PENDING_REVIEW      │    │
│  │  • Score < 50  → REJECTED            │    │
│  │  • PDF report generation (fpdf2)     │    │
│  │  • Email delivery (SendGrid)         │    │
│  └────────────────┬─────────────────────┘    │
│                   │ final_decision, report   │
│                  END                         │
└──────────────────────────────────────────────┘
```

---

## Shared State — `PractitionerState`

All three agents communicate through a single typed dictionary (`state.py`) that flows through the LangGraph pipeline. Each agent reads from it and writes its results back.

| Field | Set by | Description |
|-------|--------|-------------|
| `practitioner_id`, `full_name`, `specialty`, `country`, `registration_number`, `documents` | API | Input data from the form |
| `extracted_text`, `document_quality`, `doc_anomalies`, `document_count` | Agent 1 | OCR + structuring results |
| `extraction_json_output`, `extraction_documents_json` | Agent 1 | Full structured JSON per document |
| `trust_score`, `credential_flags`, `verification_json_output` | Agent 2 | Scoring and verification results |
| `final_decision`, `final_report`, `report_json_output` | Agent 3 | Decision + final report |
| `error_messages`, `processing_log` | All agents | Audit trail |

---

## Agent Detail

### Agent 1 — Document Extraction
- Iterates over each uploaded file
- **PDF**: extracts text with `pdfplumber`
- **Images**: runs OCR with `EasyOCR` or `pytesseract`
- Sends raw text to **Groq Llama 3.1** to structure it into a typed JSON (name, license number, institution, dates, etc.)
- Computes a quality score (0–1) based on field completeness
- Detects anomalies (missing fields, blurry images, etc.)

### Agent 2 — Credential Verification
- **Structural score**: compares extracted JSON fields against gold-standard schemas (`schemas/doctor_license.json`, `clinic_operating_license.json`, `lab_accreditation.json`)
- **Semantic score**: sends full document context to Groq LLM for logical consistency check (dates, institution names, formatting)
- **QR verification**: attempts to decode QR codes in documents for additional validation
- **Final trust score** = average of structural + semantic scores (×100)

### Agent 3 — Report & Decision
- Sends trust score + flagged issues to Groq LLM for a reasoned decision
- Falls back to threshold-based decision if LLM is unavailable
- Generates a formatted **PDF report** using `fpdf2`
- Sends the report by **email** via SendGrid REST API (async, non-blocking)
- Updates state with `final_decision` and `final_report`

---

## Frontend Flow

```
LandingPage
    │  (select role: Doctor / Clinic / Lab)
    ▼
UploadForm
    │  (fill name, license, specialty, country + upload files)
    ▼
PipelineStatus        ← shows 3 animated steps while API call is in progress
    │
    ▼
ResultsDashboard      ← displays trust score, decision, issues, next steps
```

The frontend calls `POST /api/verify` with a 120-second timeout. The three pipeline steps in the UI are cosmetic animations; the actual progress comes from the single API response.

---

## Document Type Detection

The backend auto-detects document types from filenames:

| Keyword in filename | Detected type |
|---------------------|--------------|
| `diploma`, `diplôme` | `diploma` |
| `id`, `identit`, `passport` | `id` |
| `license`, `agrément`, `licence` | `license` |
| `iso`, `accreditation` | `certification` |
| (anything else) | `document` |

---

## Decision Thresholds

| Trust Score | Decision |
|-------------|----------|
| > 85 | `APPROVED` — credentials verified automatically |
| 50 – 85 | `PENDING_REVIEW` — requires human verification |
| < 50 | `REJECTED` — credentials appear suspicious or incomplete |
