# Rapport Détaillé: Problématique 3
## Trusted Practitioner Onboarding & Verification (The Trust Bottleneck)

**Document Type:** Technical Solution Design + Team Division  
**Hackathon:** Innobyte 2.0  
**Track:** B - Digital Health Trust  
**Team Size:** 3 developers  
**Date:** 2026-05-02

---

## 📋 Résumé Exécutif

### Le Problème (The Fatal Paradox)
Les plateformes de santé numérique (Doctome) face un dilemme:

**Optimiser pour SPEED:**
- ✓ Doctors peuvent accéder rapidement
- ✗ Risque: fraude, non-vérifiés, patients en danger
- ✗ Réputation morte si un fake doctor sévit

**Optimiser pour SECURITY:**
- ✓ Vérification rigoureuse, safe
- ✗ Processus manuel = bottleneck administratif
- ✗ Doctors attendent des mois → vont voir concurrence
- ✗ Plateforme ne scale jamais (impossible expansion)

### La Solution: Intelligence Hybride
**AI-Powered Document Verification + Human-in-the-Loop**

```
Doctors soumet dossier
    ↓
AI (Groq/Claude) analyse documents + calcule Trust Score
    ↓
Decision Routing:
  Score ≥ 80 → AUTO-APPROVED (accès immédiat)
  Score 50-79 → PENDING (file d'attente humain)
  Score < 50 → REJECTED (avec feedback)
    ↓
Admins review PENDING dossiers (AI a déjà fait 80% du travail)
    ↓
Doctor accède à la plateforme
```

### Résultat: Speed + Security
- **Vitesse:** 95% des doctors approuvés en minutes (auto)
- **Sécurité:** 5% suspectes reviewées manuellement par humans
- **Scalabilité:** Peut traiter 10K doctors/jour sans augmenter staff

---

## 🎯 Architecture Haute Niveau

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                         │
│                                                                    │
│  /onboarding        → Multi-step form + file upload              │
│  /status/[id]       → Real-time verification status + score      │
│  /admin/review      → Pending applications queue                 │
│  /admin/dashboard   → Metrics + approvals trends                 │
│                                                                    │
└────────────────────┬───────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
    ┌────────────────────┐  ┌──────────────────┐
    │  Django API        │  │  Document Parser │
    │  (views, auth)     │  │  (PyMuPDF, OCR)  │
    └────────┬───────────┘  └────────┬─────────┘
             │                       │
             └───────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────────┐
            │   AI Verification Engine   │
            │   (Groq/Claude API)        │
            │   - Analyze documents      │
            │   - Calculate trust score  │
            │   - Detect anomalies       │
            │   - Generate reasoning     │
            └────────────┬───────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
    ┌──────────────┐           ┌──────────────────┐
    │  Database    │           │  Admin Dashboard │
    │  (SQLite/PG) │           │  (Review queue)  │
    └──────────────┘           └──────────────────┘
```

---

## 💾 Database Schema

```sql
-- Practitioners (main table)
CREATE TABLE practitioners (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20),
  specialty VARCHAR(100),  -- Cardiology, Pediatrics, etc
  country VARCHAR(100),
  registration_number VARCHAR(100),  -- License #
  
  status VARCHAR(50),  -- PENDING_VERIFICATION, APPROVED, REJECTED, PENDING_REVIEW
  trust_score INT,  -- 0-100
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  verified_at TIMESTAMP (when status = APPROVED),
  
  INDEX(status),
  INDEX(trust_score)
);

-- Documents (one per document type)
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  practitioner_id INT (FK to practitioners),
  document_type VARCHAR(50),  -- DIPLOMA, LICENSE, ID, INSURANCE, etc
  original_filename VARCHAR(255),
  file_path VARCHAR(500),  -- stored in /media/documents/
  file_hash VARCHAR(64),  -- SHA256 for integrity
  extracted_text LONGTEXT,  -- OCR/text extraction result
  upload_date TIMESTAMP DEFAULT NOW(),
  
  FOREIGN KEY (practitioner_id) REFERENCES practitioners(id)
);

-- TrustAssessment (AI analysis result)
CREATE TABLE trust_assessments (
  id SERIAL PRIMARY KEY,
  practitioner_id INT (FK to practitioners),
  
  -- AI Analysis Results
  trust_score INT (0-100),
  decision VARCHAR(50),  -- AUTO_APPROVED, PENDING_REVIEW, REJECTED
  ai_reasoning TEXT,  -- Why this decision
  flags JSON,  -- ["name_inconsistency", "document_missing", etc]
  missing_documents JSON,  -- ["LICENSE", "INSURANCE"]
  
  -- AI Metadata
  model_used VARCHAR(50),  -- "groq-llama-3.1", "claude-3.5", etc
  confidence_score DECIMAL(3,2),  -- 0.0-1.0
  analysis_timestamp TIMESTAMP DEFAULT NOW(),
  
  -- Human Review (if PENDING_REVIEW)
  reviewed_by_admin_id INT (nullable, FK to users),
  review_decision VARCHAR(50),  -- APPROVED, REJECTED (if human overrides)
  review_notes TEXT,
  reviewed_at TIMESTAMP (nullable),
  
  FOREIGN KEY (practitioner_id) REFERENCES practitioners(id)
);

-- AdminActions (audit trail)
CREATE TABLE admin_actions (
  id SERIAL PRIMARY KEY,
  practitioner_id INT,
  admin_id INT,
  action VARCHAR(100),  -- APPROVED, REJECTED, COMMENT_ADDED, etc
  notes TEXT,
  timestamp TIMESTAMP DEFAULT NOW(),
  
  FOREIGN KEY (practitioner_id) REFERENCES practitioners(id)
);

-- Users (admin users)
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255),
  role VARCHAR(50),  -- admin, reviewer, superadmin
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🏗️ Composants Système

### 1. Frontend (Next.js 14)

**Pages:**
```
app/
  page.tsx                    ← Homepage/landing
  onboarding/
    page.tsx                  ← Multi-step form
    layout.tsx
  status/
    [id]/
      page.tsx                ← Status tracking page
  admin/
    login/page.tsx            ← Admin authentication
    review/
      page.tsx                ← Queue des dossiers PENDING
      [id]/page.tsx           ← Individual review modal
    dashboard/
      page.tsx                ← Analytics dashboard
    settings/page.tsx         ← Admin configuration
```

**Components Réutilisables:**
```
components/
  FileUpload.tsx              ← Drag & drop file upload
  DocumentViewer.tsx          ← Show uploaded documents
  TrustScoreDisplay.tsx       ← Visual trust score (0-100)
  StatusBadge.tsx             ← Status indicator
  ReviewModal.tsx             ← Admin review interface
  DashboardMetrics.tsx        ← Stats & charts
  AuditLog.tsx                ← Timeline of actions
```

### 2. Backend (Django + DRF)

**APIs:**
```
POST   /api/v1/practitioners/submit/           ← Create new application
GET    /api/v1/practitioners/{id}/             ← Get application status
GET    /api/v1/practitioners/{id}/documents/   ← List uploaded docs
GET    /api/v1/admin/pending/                  ← List pending reviews
POST   /api/v1/admin/{id}/approve/            ← Admin approval
POST   /api/v1/admin/{id}/reject/             ← Admin rejection
GET    /api/v1/admin/stats/                    ← Dashboard metrics
POST   /api/v1/admin/{id}/comments/           ← Add review comments
```

**Django Apps:**
```
practitioners/
  models.py
  views.py
  serializers.py
  urls.py
  
  ai_verification/
    verifier.py               ← Groq integration
    document_parser.py        ← PyMuPDF + OCR
    trust_calculator.py       ← Logic for trust score

  admin/
    views.py                  ← Admin endpoints
    admin_serializers.py
```

### 3. AI Verification Engine

**Groq Integration:**
```python
# ai_verification/verifier.py

class PractitionerVerifier:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-70b-versatile"
    
    def verify(self, practitioner_data, documents_text):
        """
        Main verification method.
        Input: practitioner info + extracted text from documents
        Output: {trust_score, decision, flags, reasoning}
        """
        prompt = self._build_verification_prompt(
            practitioner_data,
            documents_text
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content": SYSTEM_PROMPT,
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.2,  # Low = consistent
            max_tokens=800,
        )
        
        result = self._parse_ai_response(response.choices[0].message.content)
        return result
    
    def _build_verification_prompt(self, practitioner, docs_text):
        return f"""
        Verify this healthcare practitioner:
        
        Declared Information:
        - Name: {practitioner['full_name']}
        - Specialty: {practitioner['specialty']}
        - Country: {practitioner['country']}
        - License #: {practitioner['registration_number']}
        
        Documents Provided (extracted text):
        {docs_text[:3000]}  # Limit to 3000 chars for tokens
        
        Evaluate:
        1. Information consistency across documents
        2. Medical credential validity
        3. License/registration validity for stated country
        4. Document anomalies (dates, names, institutions)
        5. Completeness (all required docs present?)
        
        Output ONLY valid JSON:
        {{
          "trust_score": <0-100>,
          "decision": "<AUTO_APPROVED|PENDING_REVIEW|REJECTED>",
          "flags": ["<flag1>", "<flag2>"],
          "missing_documents": ["<doc_type>"],
          "reasoning": "<brief explanation>"
        }}
        """
```

---

## 🔄 Workflow Complet: Cas d'Usage

### Scenario: Doctor registers pour Doctome

```
MINUTE 0: Doctor visits platform
┌─────────────────────────────────────────┐
│ /onboarding page loads                  │
│                                         │
│ STEP 1: Personal Information            │
│  [Full Name] [Email] [Phone]           │
│  [Specialty] [Country] [License #]     │
│                                         │
│ STEP 2: Upload Documents                │
│  [Drag & drop]                         │
│  - Medical Diploma (PDF)               │
│  - License/Order (PDF)                 │
│  - ID Card (JPG/PNG)                   │
│  - Insurance/Liability (PDF)           │
│                                         │
│ STEP 3: Confirmation                    │
│  "Review and submit application"       │
│  [Submit Button]                       │
└──────────────┬──────────────────────────┘
               │
MINUTE 0.5: Backend receives application
┌─────────────────────────────────────────┐
│ Django API validates input              │
│ ✓ Email valid, unique                   │
│ ✓ All required fields filled            │
│ ✓ Documents uploaded (4 files)          │
│                                         │
│ Creates Practitioner record:            │
│  ID: #4521                              │
│  Status: PENDING_VERIFICATION           │
│  Trust Score: null (pending AI)         │
└──────────────┬──────────────────────────┘
               │
MINUTE 0.5-1: Document Processing
┌─────────────────────────────────────────┐
│ For each document:                      │
│                                         │
│ 1. Save file to /media/documents/      │
│ 2. Extract text (PyMuPDF + OCR)        │
│    Diploma PDF → "Dr. Ahmed Ben Ali    │
│                  Graduated 2015        │
│                  Cardiology..."        │
│                                         │
│ 3. Store extracted_text in DB          │
│                                         │
│ 4. Concatenate all text for AI         │
└──────────────┬──────────────────────────┘
               │
MINUTE 1-3: AI Verification (Groq)
┌─────────────────────────────────────────┐
│ Groq Llama analyzes:                    │
│                                         │
│ "Name 'Ahmed Ben Ali' consistent?      │
│  ✓ Diploma: Ahmed Ben Ali              │
│  ✓ License: A. Ben Ali Ahmed           │
│  ✓ ID: Ahmed Ali Ben                   │
│  ⚠ Order slightly different             │
│                                         │
│  Specialty 'Cardiology' valid?          │
│  ✓ Diploma: Cardiology                 │
│  ✓ License: Cardiologie (French)       │
│  ✓ Match                                │
│                                         │
│  Dates make sense?                      │
│  ✓ Graduated 2015 ≤ License 2016       │
│  ✓ License valid until 2026             │
│  ✓ Timeline OK                          │
│                                         │
│  Document quality?                      │
│  ✓ All official institutions           │
│  ✓ No obvious forgeries                │
│  ✓ Timestamps coherent                 │
│                                         │
│  Result:                                │
│  {                                      │
│    "trust_score": 84,                   │
│    "decision": "AUTO_APPROVED",         │
│    "flags": ["name_order_variation"],   │
│    "reasoning": "All creds verified,   │
│     minor name variation normal"        │
│  }                                      │
└──────────────┬──────────────────────────┘
               │
MINUTE 3: Auto-Approval Decision
┌─────────────────────────────────────────┐
│ Trust Score ≥ 80? YES                   │
│ → AUTO_APPROVED                         │
│                                         │
│ Update database:                        │
│  practitioners.status = "APPROVED"      │
│  practitioners.trust_score = 84         │
│  practitioners.verified_at = NOW()      │
│                                         │
│ Create TrustAssessment record:          │
│  - ai_reasoning: "..."                 │
│  - flags: ["name_order_variation"]     │
│  - confidence_score: 0.92               │
└──────────────┬──────────────────────────┘
               │
MINUTE 3+: Doctor Notification
┌─────────────────────────────────────────┐
│ Email sent to doctor:                   │
│ "✓ Your application approved!          │
│  You can now access Doctome.            │
│  Trust Score: 84/100                    │
│  You're verified as Cardiologist"       │
│                                         │
│ Doctor sees on /status/4521:            │
│ ┌─────────────────────────────────┐   │
│ │ Application Status              │   │
│ │                                 │   │
│ │ Status: ✓ APPROVED              │   │
│ │ Trust Score: [████████░] 84/100│   │
│ │                                 │   │
│ │ Documents Verified:             │   │
│ │ ✓ Medical Diploma               │   │
│ │ ✓ License/Order                 │   │
│ │ ✓ ID Card                       │   │
│ │ ✓ Insurance                     │   │
│ │                                 │   │
│ │ AI Reasoning:                   │   │
│ │ "All credentials verified,      │   │
│ │  minor name variation expected" │   │
│ │                                 │   │
│ │ [Access Platform →]             │   │
│ └─────────────────────────────────┘   │
│                                         │
│ Doctor immediately can:                 │
│ - Create clinic profile                │
│ - Setup availability                   │
│ - Accept patients                      │
│ - Start consultations                  │
└─────────────────────────────────────────┘

MINUTE ~0.5 FOR AUTO-APPROVED CASES (95% of good applications)
```

### Cas Alternative: PENDING_REVIEW (Trust Score 50-79)

```
Groq returns trust_score = 67 (suspicious):
{
  "decision": "PENDING_REVIEW",
  "flags": ["name_inconsistency", "license_country_mismatch"],
  "trust_score": 67
}

Doctor sees:
┌──────────────────────────────────┐
│ Status: ⏳ UNDER REVIEW           │
│ Trust Score: [███████░░] 67/100 │
│                                  │
│ ⚠ Review Needed:                 │
│ - Name spelling varies between   │
│   documents                      │
│ - License from different country │
│                                  │
│ We're verifying your credentials.│
│ Typically 24-48 hours.           │
│                                  │
│ Questions? Contact support@      │
└──────────────────────────────────┘

Admin sees in /admin/review:
┌────────────────────────────────────────┐
│ Pending Reviews (12)                   │
├─────────────┬──────────┬────────────┤
│ Doctor Name │ Score    │ Flag       │
├─────────────┼──────────┼────────────┤
│ Ahmed Ben.. │ 67       │ ⚠ Name inc │
│ Fatima X..  │ 55       │ ⚠ 2 flags │
│ Dr. Y...    │ 73       │ ⚠ 1 flag  │
└─────────────┴──────────┴────────────┘

Admin clicks → modal:
┌────────────────────────────────────────┐
│ Dr. Ahmed Ben Ali (ID #4521)           │
│                                        │
│ Trust Score: 67/100                    │
│ Flags: name_inconsistency              │
│        license_country_mismatch        │
│                                        │
│ AI Reasoning:                          │
│ "Name spelled 'Ahmed Ben Ali' in      │
│  diploma but 'A. Ben-Ali' in license. │
│  License from Morocco (not Algeria).  │
│  Requires human verification."        │
│                                        │
│ Documents:                             │
│ [View Diploma] [View License]         │
│ [View ID] [View Insurance]            │
│                                        │
│ Admin Actions:                         │
│ [✓ Approve] [✗ Reject]               │
│ [Add Note...]                         │
│                                        │
│ Admin reviews:                         │
│ "Name variation OK (common in North   │
│  Africa). Morocco license valid.      │
│ Context: Practicing in Algeria since  │
│ 2018 (no issues)."                    │
│                                        │
│ → Clicks [✓ Approve]                 │
│                                        │
│ Status changes: PENDING_REVIEW        │
│                         ↓             │
│                     APPROVED         │
│                                        │
│ Email sent: "Your application         │
│ approved by our team."               │
└────────────────────────────────────────┘
```

---

## 👥 Division du Travail: 3 Personnes

### Team Structure

```
Team:
  Person A: Backend Lead (Django + AI Integration)
  Person B: Frontend Lead (Next.js UI/UX)
  Person C: DevOps/Database + Support
```

---

## 🔧 PERSON A: Backend Lead & AI Integration

### Responsibilities
1. Django project setup & architecture
2. Database models & migrations
3. Groq AI integration (core logic)
4. Document processing pipeline
5. Trust score calculation algorithm
6. API endpoints design & implementation
7. Authentication/authorization

### Detailed Tasks

**Week 1-2: Foundation (16-20 hours)**

```
Task 1: Django Project Setup (2 hours)
├─ Initialize Django project
├─ Configure settings (DB, email, etc)
├─ Setup virtual environment
├─ Create Django apps: practitioners, ai_verification, admin
└─ Git repository + initial commit

Task 2: Database Schema & Models (4 hours)
├─ Create models: Practitioner, Document, TrustAssessment
├─ Create migrations
├─ Add indexes for performance
├─ Setup relationships (ForeignKeys)
└─ Test models locally

Task 3: Document Parser Module (4 hours)
├─ Install PyMuPDF (PDF extraction)
├─ Write document_parser.py
├─ Handle text extraction from PDFs
├─ Handle image OCR (Tesseract optional)
├─ Store extracted text in DB
└─ Test with sample documents

Task 4: Groq AI Integration (5 hours)
├─ Setup Groq API key
├─ Write verifier.py class
├─ Build verification prompt template
├─ Handle Groq API calls
├─ Parse JSON responses
├─ Error handling (API failures, bad JSON)
├─ Test with mock documents
└─ Log AI responses for debugging

Task 5: Core API Endpoints (5 hours)
├─ POST /api/v1/practitioners/submit/
│  ├─ Receive form data + files
│  ├─ Validate inputs
│  ├─ Create Practitioner record
│  ├─ Trigger document processing
│  ├─ Call AI verification
│  └─ Return application ID
├─
├─ GET /api/v1/practitioners/{id}/
│  ├─ Return current status
│  ├─ Return trust score
│  ├─ Return trust reasoning
│  └─ Handle not-found errors
└─ Test all endpoints with Postman
```

**Week 2-3: AI & Business Logic (16-20 hours)**

```
Task 6: Trust Score Calculation (3 hours)
├─ Implement scoring algorithm
├─ Parse AI response from Groq
├─ Extract trust_score value
├─ Validate range (0-100)
├─ Extract flags/warnings
├─ Store in TrustAssessment table
└─ Add logging for debugging

Task 7: Decision Routing Logic (4 hours)
├─ Implement routing rules:
│  ├─ IF score ≥ 80 → AUTO_APPROVED
│  ├─ IF 50 ≤ score < 80 → PENDING_REVIEW
│  └─ IF score < 50 → REJECTED
├─ Update practitioner.status
├─ Generate rejection reason
├─ Create admin_actions log entry
└─ Test all three branches

Task 8: Admin APIs (5 hours)
├─ GET /api/v1/admin/pending/
│  ├─ List all PENDING_REVIEW applications
│  ├─ Include trust_score, flags
│  ├─ Include extracted document text
│  └─ Pagination + filtering
├─
├─ POST /api/v1/admin/{id}/approve/
│  ├─ Validate admin user
│  ├─ Update status to APPROVED
│  ├─ Create admin_actions log
│  └─ Send approval email
├─
├─ POST /api/v1/admin/{id}/reject/
│  ├─ Validate admin user
│  ├─ Update status to REJECTED
│  ├─ Store rejection reason
│  └─ Send rejection email with reason
└─ Add admin authentication (JWT or session)

Task 9: Email Notifications (3 hours)
├─ Setup Django email backend
├─ Create email templates:
│  ├─ auto_approved.html
│  ├─ pending_review.html
│  └─ rejected.html
├─ Send emails on status changes
└─ Test email functionality

Task 10: Testing & Debugging (5 hours)
├─ Write unit tests for AI verifier
├─ Write tests for trust calculation
├─ Write tests for routing logic
├─ Write integration tests (E2E)
├─ Fix bugs discovered
└─ Performance optimization (PyMuPDF speed)
```

### Code Samples (Person A)

**models.py**
```python
from django.db import models

class Practitioner(models.Model):
    STATUS_CHOICES = [
        ('PENDING_VERIFICATION', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PENDING_REVIEW', 'Pending Review'),
    ]
    
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    specialty = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=100)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_VERIFICATION')
    trust_score = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['trust_score']),
        ]
```

**ai_verification/verifier.py**
```python
import json
from groq import Groq
import os

class PractitionerVerifier:
    def __init__(self):
        self.client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        self.model = "llama-3.1-70b-versatile"
    
    def verify(self, practitioner, documents_text):
        prompt = self._build_prompt(practitioner, documents_text)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a medical credential verification expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800,
        )
        
        result = self._parse_response(response.choices[0].message.content)
        return result
    
    def _build_prompt(self, practitioner, documents_text):
        return f"""
Verify this healthcare practitioner application:

Declared Information:
- Name: {practitioner.full_name}
- Specialty: {practitioner.specialty}
- Country: {practitioner.country}
- License #: {practitioner.registration_number}

Extracted Document Text:
{documents_text[:3000]}

Evaluate:
1. Consistency of name/specialty across documents
2. Medical credential validity
3. Document authenticity indicators
4. Completeness of required documents
5. Any anomalies or red flags

Output ONLY valid JSON:
{{
  "trust_score": <0-100>,
  "decision": "<AUTO_APPROVED|PENDING_REVIEW|REJECTED>",
  "flags": ["<flag1>"],
  "missing_documents": [],
  "reasoning": "<brief explanation>"
}}
"""
    
    def _parse_response(self, content):
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content.strip())
            return result
        except:
            return {
                "trust_score": 50,
                "decision": "PENDING_REVIEW",
                "flags": ["ai_parsing_error"],
                "reasoning": "Unable to parse AI response"
            }
```

---

## 🎨 PERSON B: Frontend Lead (Next.js/React)

### Responsibilities
1. Next.js project setup
2. UI component library (Tailwind)
3. Onboarding form (multi-step)
4. Status tracking page
5. Admin dashboard (review queue)
6. Analytics dashboard
7. Responsive design + mobile

### Detailed Tasks

**Week 1-2: Foundation & Onboarding (16-20 hours)**

```
Task 1: Next.js Project Setup (2 hours)
├─ Create Next.js 14 project
├─ Setup Tailwind CSS
├─ Setup directory structure
├─ Configure environment variables
├─ Setup API communication (axios/fetch)
└─ Git repository + initial commit

Task 2: Onboarding Form (6 hours)
├─ Create /onboarding/page.tsx
├─ Step 1: Personal info form
│  ├─ Name, Email, Phone inputs
│  ├─ Specialty dropdown
│  ├─ Country dropdown
│  └─ License # input
├─ Step 2: Document upload
│  ├─ Drag & drop file upload
│  ├─ Show uploaded files
│  ├─ File validation (PDF/JPG only)
│  ├─ Show file size limits
│  └─ Visual feedback
├─ Step 3: Review & Submit
│  ├─ Show entered info summary
│  ├─ Show uploaded docs
│  ├─ [Submit] button
│  └─ Loading state during submit
├─ Form validation (client-side)
├─ Error handling & messages
└─ Beautiful UI with Tailwind

Task 3: Status Tracking Page (5 hours)
├─ Create /status/[id]/page.tsx
├─ Display current status badge
├─ Display trust score (visual bar)
├─ Display AI reasoning
├─ Show each document + verification status
├─ Show timeline of actions
├─ Auto-refresh status (polling every 5s)
├─ Show action buttons if PENDING_REVIEW
└─ Responsive design

Task 4: Component Library (4 hours)
├─ Create components/
├─ TrustScoreBadge.tsx (visual score display)
├─ FileUpload.tsx (reusable upload)
├─ StatusBadge.tsx (status indicator)
├─ LoadingSpinner.tsx
├─ DocumentCard.tsx (document display)
└─ Test all components

Task 5: Styling & Responsive (3 hours)
├─ Setup Tailwind configuration
├─ Create color scheme (trust = green)
├─ Create reusable classes
├─ Test mobile responsiveness
├─ Dark mode support (optional)
└─ Fix layout issues
```

**Week 2-3: Admin & Dashboard (16-20 hours)**

```
Task 6: Admin Authentication (3 hours)
├─ Create /admin/login/page.tsx
├─ Login form with email/password
├─ JWT token storage (localStorage)
├─ Protected routes middleware
├─ Logout functionality
└─ Handle auth errors

Task 7: Admin Review Queue (7 hours)
├─ Create /admin/review/page.tsx
├─ Display list of PENDING_REVIEW applications
├─ Show: Doctor name, trust score, flags
├─ Clickable rows → modal view
├─ Modal shows:
│  ├─ Full doctor details
│  ├─ Trust score + reasoning
│  ├─ All documents (embedded viewer)
│  ├─ Flags/warnings highlighted
│  ├─ [Approve] [Reject] buttons
│  └─ Comment text area
├─ Form validation
├─ Success/error messages
├─ Refresh list after action
└─ Pagination

Task 8: Admin Dashboard (6 hours)
├─ Create /admin/dashboard/page.tsx
├─ Show key metrics:
│  ├─ Total applications
│  ├─ Approved count
│  ├─ Pending count
│  ├─ Rejection rate
│  ├─ Average trust score
│  └─ Approval time (avg)
├─ Charts:
│  ├─ Trust score distribution (histogram)
│  ├─ Status breakdown (pie chart)
│  ├─ Approvals over time (line chart)
│  └─ Rejection reasons (bar chart)
├─ Integrate with recharts
├─ Make charts interactive
└─ Filter by date range

Task 9: API Integration (5 hours)
├─ Create api/ folder with:
│  ├─ practitioners.ts (GET /status, POST /submit)
│  ├─ admin.ts (GET /pending, POST /approve, POST /reject)
│  └─ stats.ts (GET /stats)
├─ Handle loading states
├─ Error handling + retry logic
├─ Axios interceptors for auth tokens
└─ Type definitions (TypeScript)

Task 10: Testing & Refinement (4 hours)
├─ Test all forms end-to-end
├─ Test responsive design (mobile/tablet/desktop)
├─ Fix UI bugs
├─ Performance optimization
├─ Accessibility review (A11y)
└─ Cross-browser testing (Chrome, Firefox, Safari)
```

### Code Samples (Person B)

**app/onboarding/page.tsx**
```typescript
'use client'
import { useState } from 'react'
import axios from 'axios'

export default function OnboardingPage() {
  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    specialty: '',
    country: '',
    registration_number: ''
  })
  const [documents, setDocuments] = useState<File[]>([])
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    const formDataToSend = new FormData()
    Object.entries(formData).forEach(([key, value]) => {
      formDataToSend.append(key, value as string)
    })
    documents.forEach((doc) => {
      formDataToSend.append('documents', doc)
    })

    try {
      const response = await axios.post(
        '/api/v1/practitioners/submit/',
        formDataToSend,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      window.location.href = `/status/${response.data.id}`
    } catch (error) {
      alert('Error submitting application')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-4xl font-bold mb-6">Practitioner Registration</h1>
      
      {step === 1 && (
        <form onSubmit={(e) => { e.preventDefault(); setStep(2) }}>
          <input
            type="text"
            placeholder="Full Name"
            value={formData.full_name}
            onChange={(e) => setFormData({...formData, full_name: e.target.value})}
            className="w-full p-3 border rounded mb-4"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="w-full p-3 border rounded mb-4"
            required
          />
          <select
            value={formData.specialty}
            onChange={(e) => setFormData({...formData, specialty: e.target.value})}
            className="w-full p-3 border rounded mb-4"
            required
          >
            <option value="">Select Specialty</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Pediatrics">Pediatrics</option>
            <option value="Surgery">Surgery</option>
          </select>
          <button
            type="submit"
            className="w-full bg-blue-600 text-white p-3 rounded font-bold hover:bg-blue-700"
          >
            Next: Upload Documents
          </button>
        </form>
      )}

      {step === 2 && (
        <form onSubmit={handleSubmit}>
          <div className="border-2 border-dashed p-8 rounded text-center mb-4">
            <input
              type="file"
              multiple
              onChange={(e) => setDocuments(Array.from(e.target.files || []))}
              className="hidden"
              id="fileInput"
              accept=".pdf,.jpg,.jpeg,.png"
            />
            <label htmlFor="fileInput" className="cursor-pointer">
              <p className="text-lg font-semibold">Drag files here or click to upload</p>
              <p className="text-sm text-gray-500">Accepted: PDF, JPG, PNG</p>
            </label>
            {documents.length > 0 && (
              <div className="mt-4">
                <h3 className="font-semibold">Uploaded Files:</h3>
                {documents.map((doc, i) => (
                  <p key={i} className="text-sm text-gray-600">{doc.name}</p>
                ))}
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={loading || documents.length === 0}
            className="w-full bg-green-600 text-white p-3 rounded font-bold hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit Application'}
          </button>
        </form>
      )}
    </div>
  )
}
```

---

## 🗄️ PERSON C: DevOps, Database & Full-Stack Support

### Responsibilities
1. Database setup & optimization
2. Environment setup (local dev, staging, production)
3. CI/CD pipeline setup
4. Deployment & hosting
5. Performance monitoring
6. Security hardening
7. Full-stack support (help A & B)
8. Testing infrastructure

### Detailed Tasks

**Week 1-2: Infrastructure & Database (16-20 hours)**

```
Task 1: Local Development Environment (3 hours)
├─ Docker setup for PostgreSQL
├─ Docker setup for Redis (caching)
├─ Docker Compose configuration
├─ .env files setup
├─ README with setup instructions
└─ Test that everything runs locally

Task 2: Database Schema & Optimization (5 hours)
├─ Create all tables (from Person A's models)
├─ Add indexes for performance:
│  ├─ Index on practitioners.status
│  ├─ Index on practitioners.trust_score
│  ├─ Index on documents.practitioner_id
│  ├─ Index on trust_assessments.practitioner_id
│  └─ Index on admin_actions.practitioner_id
├─ Setup auto-increments
├─ Add constraints (NOT NULL, UNIQUE, FK)
├─ Write migration scripts
├─ Test migrations work
└─ Setup database backups

Task 3: File Storage (3 hours)
├─ Setup /media directory for document storage
├─ Configure file permissions (secure)
├─ Setup virus scanning for uploads (optional)
├─ Configure file cleanup (old files)
├─ Test file upload/download
└─ Backup strategy for documents

Task 4: Authentication & Security (4 hours)
├─ Setup JWT authentication
├─ Configure CORS (frontend domain)
├─ Setup password hashing (bcrypt)
├─ Add rate limiting (prevent brute force)
├─ Setup HTTPS/SSL (self-signed for dev)
├─ Add input validation/sanitization
├─ Test security measures
└─ Document security practices

Task 5: Logging & Monitoring (3 hours)
├─ Setup structured logging (Python logging)
├─ Log all AI API calls (for debugging)
├─ Log all admin actions
├─ Log all API errors
├─ Configure log rotation
├─ Setup error tracking (Sentry or similar)
└─ Create monitoring dashboard
```

**Week 2-3: CI/CD & Deployment (16-20 hours)**

```
Task 6: Git Workflow & CI Pipeline (5 hours)
├─ Setup GitHub Actions
├─ Create workflow for:
│  ├─ Run tests on every PR
│  ├─ Lint code (flake8, eslint)
│  ├─ Type checking (mypy, tsc)
│  └─ Security scanning
├─ Configure branch protection rules
├─ Setup auto-deploy on merge to main
└─ Test CI pipeline

Task 7: Staging Deployment (5 hours)
├─ Setup staging environment (Railway, Vercel, or AWS)
├─ Deploy Django backend to staging
├─ Deploy Next.js frontend to staging
├─ Configure database for staging (separate from prod)
├─ Test full stack on staging
├─ Setup email backend for staging
└─ Document deployment process

Task 8: Production Deployment (5 hours)
├─ Setup production environment
├─ Configure production database (PostgreSQL)
├─ Setup SSL certificates
├─ Configure domain names
├─ Deploy Django backend (Gunicorn + Nginx)
├─ Deploy Next.js frontend
├─ Setup CDN for static files
├─ Test production deployment
└─ Create runbook for common issues

Task 9: Performance Optimization (5 hours)
├─ Database query optimization:
│  ├─ N+1 query fixes
│  ├─ Query caching
│  ├─ Index verification
│  └─ Slow query logs
├─ API response time monitoring
├─ Frontend performance:
│  ├─ Code splitting
│  ├─ Image optimization
│  └─ Bundle size analysis
├─ Caching strategy (Redis)
└─ Load testing

Task 10: Monitoring & Alerts (3 hours)
├─ Setup uptime monitoring
├─ Setup error alerts (Slack notification)
├─ Setup performance alerts
├─ Create status page (public)
├─ Setup database backup verification
└─ Document troubleshooting guide
```

### Code Samples (Person C)

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: practitioner_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: practitioner_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U practitioner_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  django:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://practitioner_user:secure_password@postgres:5432/practitioner_db
      REDIS_URL: redis://redis:6379

  nextjs:
    build: ./frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    depends_on:
      - django

volumes:
  postgres_data:
```

**.github/workflows/ci.yml**
```yaml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          python manage.py test
      
      - name: Lint
        run: |
          cd backend
          flake8 . --max-line-length=100
      
      - name: Type check
        run: |
          cd backend
          mypy . --ignore-missing-imports
```

---

## 📅 Timeline Consolidated: 3 Personnes

### Week 1

```
PERSON A (Backend):
  Day 1-2: Django setup + DB models
  Day 3-4: Document parser (PyMuPDF)
  Day 5: Groq integration basics

PERSON B (Frontend):
  Day 1-2: Next.js setup + Tailwind
  Day 3-4: Onboarding form (steps 1-2)
  Day 5: Status page basics

PERSON C (DevOps):
  Day 1-2: Docker + PostgreSQL setup
  Day 3-4: CI/CD pipeline (GitHub Actions)
  Day 5: Database optimization
  
SYNC POINT (End of Week 1):
  - Backend API endpoints working
  - Frontend form collecting data
  - Both can communicate (API calls test)
  - Database schema finalized
```

### Week 2

```
PERSON A (Backend):
  Day 1-2: AI verification endpoint (core)
  Day 3-4: Admin endpoints (review, approve, reject)
  Day 5: Email notifications + testing

PERSON B (Frontend):
  Day 1-2: Admin review queue page
  Day 3-4: Admin dashboard (metrics + charts)
  Day 5: Authentication page + styling

PERSON C (DevOps):
  Day 1-2: Staging deployment setup
  Day 3-4: Production deployment
  Day 5: Performance optimization + monitoring

SYNC POINT (End of Week 2):
  - Full system working end-to-end
  - Can deploy to staging
  - Admin review workflow functional
  - Ready for testing
```

### Week 3 (Final Polish)

```
PERSON A (Backend):
  Day 1: Bug fixes from testing
  Day 2-3: Performance optimization
  Day 4-5: Documentation + edge cases

PERSON B (Frontend):
  Day 1: Bug fixes + responsive design fixes
  Day 2-3: UI polish + animations
  Day 4-5: Accessibility + final review

PERSON C (DevOps):
  Day 1: Production hardening
  Day 2-3: Load testing + scaling tests
  Day 4-5: Final deployment + documentation

FINAL SYNC:
  - Code review across team
  - End-to-end testing in production
  - Documentation complete
  - Ready for demo/launch
```

---

## 🚀 Daily Communication Plan

### Daily Standup (10 min, 9:00 AM)
```
Each person answers:
1. What I completed yesterday
2. What I'm working on today
3. Blockers/help needed

Example:
  Person A: "Finished AI verifier, starting admin endpoints. 
             Need Person B to finalize API contract."
  Person B: "Onboarding form working, need API docs for status page."
  Person C: "Docker setup done, created shared dev environment."
```

### Sync Meetings (2x per week, 30 min)
```
Monday: Architecture/blocking issues
Friday: Progress review + next week planning
```

### Shared Documents
```
- Notion board: Task assignments + status
- API documentation (Person A owns, updates regularly)
- UI component specs (Person B owns)
- Deployment guide (Person C owns)
```

---

## 📊 Success Metrics (for Hackathon)

```
✓ Feature Completion:
  □ Onboarding form working
  □ Document upload functional
  □ AI verification live (Groq API)
  □ Admin review queue visible
  □ Status tracking real-time
  □ Dashboard with metrics

✓ Code Quality:
  □ No blocking bugs
  □ Tests covering main flows
  □ Code documented
  □ Clean git history

✓ Performance:
  □ API response < 1 second
  □ Frontend load < 2 seconds
  □ AI analysis < 5 seconds

✓ Deployment:
  □ Works locally (docker-compose)
  □ Works on staging
  □ Works in production
```

---

## 🎯 Deliverables

```
By End of Hackathon:
  ✓ Working application (deployed)
  ✓ 3-minute demo video
  ✓ GitHub repo with clean commits
  ✓ API documentation
  ✓ Deployment guide
  ✓ Presentation slides (use case + metrics)
  ✓ Team reflection document
```

---

**Prepared by:** Claude Code  
**For:** Innobyte 2.0 Hackathon  
**Track:** B - Digital Health Trust  
**Team:** 3 Developers (Full-Stack)
