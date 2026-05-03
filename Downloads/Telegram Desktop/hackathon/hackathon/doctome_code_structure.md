# Structure du Projet: Doctome (Domaine Médical)

## Arborescence Complète

```
doctome/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   │
│   ├── practitioners/
│   │   ├── models.py                 # DB models
│   │   ├── serializers.py            # API serializers
│   │   ├── views.py                  # API views
│   │   └── urls.py                   # Routes
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Base class
│   │   ├── orchestrator.py           # Coordinator
│   │   │
│   │   ├── document_analyzer/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # DocumentAnalyzer
│   │   │   └── tools.py              # PDF, OCR tools
│   │   │
│   │   ├── credential_verifier/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # CredentialVerifier
│   │   │   └── external_apis.py      # License verification
│   │   │
│   │   ├── risk_assessor/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # RiskAssessor
│   │   │   └── ml_models.py          # ML anomaly detection
│   │   │
│   │   └── decision_engine/
│   │       ├── __init__.py
│   │       ├── agent.py              # DecisionEngine
│   │       └── rules.py              # Decision rules
│   │
│   ├── utils/
│   │   ├── logger.py
│   │   ├── audit.py
│   │   └── email.py
│   │
│   └── media/
│       └── documents/                # Uploaded files
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                  # Homepage
│   │   ├── layout.tsx
│   │   │
│   │   ├── onboarding/
│   │   │   └── page.tsx              # Registration form
│   │   │
│   │   ├── status/
│   │   │   └── [id]/page.tsx         # Status tracking
│   │   │
│   │   └── admin/
│   │       ├── login/page.tsx
│   │       ├── review/page.tsx       # Review queue
│   │       └── dashboard/page.tsx    # Analytics
│   │
│   ├── components/
│   │   ├── FileUpload.tsx
│   │   ├── TrustScoreBadge.tsx
│   │   └── ReviewModal.tsx
│   │
│   └── api/
│       └── client.ts                 # API calls
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## Files à Créer (16 fichiers principaux)

1. `backend/agents/base_agent.py`
2. `backend/agents/orchestrator.py`
3. `backend/agents/document_analyzer/agent.py`
4. `backend/agents/document_analyzer/tools.py`
5. `backend/agents/credential_verifier/agent.py`
6. `backend/agents/credential_verifier/external_apis.py`
7. `backend/agents/risk_assessor/agent.py`
8. `backend/agents/risk_assessor/ml_models.py`
9. `backend/agents/decision_engine/agent.py`
10. `backend/agents/decision_engine/rules.py`
11. `backend/practitioners/models.py`
12. `backend/practitioners/views.py`
13. `backend/config/settings.py`
14. `backend/requirements.txt`
15. `docker-compose.yml`
16. `frontend/app/onboarding/page.tsx`

On commence?
