# Doctome LangGraph - Code Structure

```
doctome_langgraph/
├── agents/                          # All verification agents
│   ├── __init__.py                 # Package initialization
│   ├── state.py                    # Shared state definition (PractitionerState)
│   ├── agent1_extraction.py        # Document extraction & analysis
│   ├── agent2_verification.py      # Credential verification
│   └── agent3_risk_assessment.py   # Risk assessment & trust scoring
│
├── data/                            # Input PDFs and documents
│   ├── DOCTOR_DIPLOMA_FR.pdf
│   ├── ALGERIAN_MEDICAL_LICENSE.pdf
│   ├── HOSPITAL_LICENSE.pdf
│   ├── LABORATORY_ACCREDITATION.pdf
│   ├── CHEIKHAOUI_AHMED_MAHDI_credential.pdf
│   └── doctor_credential_test.pdf
│
├── output/                          # Generated JSON extraction results
│   ├── DOCTOR_DIPLOMA_FR_extraction.json
│   ├── ALGERIAN_MEDICAL_LICENSE_extraction.json
│   ├── HOSPITAL_LICENSE_extraction.json
│   ├── LABORATORY_ACCREDITATION_extraction.json
│   └── extraction_summary.json
│
├── graph.py                         # LangGraph workflow orchestrator
├── generate_test_pdfs.py           # Generate realistic test PDFs
└── LANGGRAPH_README.md             # Documentation
```

## Running the System

### Test Agent 1 (Extraction)
```bash
cd doctome_langgraph
python -m agents.agent1_extraction
```

### Run Full Workflow
```bash
python graph.py
```

### Generate Test PDFs
```bash
python generate_test_pdfs.py
```

## Module Imports

```python
# From agents package
from agents import PractitionerState, extraction_agent
from agents import verification_agent, risk_assessment_agent

# Or directly
from agents.agent1_extraction import extraction_agent
from agents.state import PractitionerState
```
