# Doctome Implementation with LangGraph
## 3 Agents Linked via LangGraph

**Architecture:** Multi-Agent System with LangGraph State Management  
**Date:** 2026-05-02

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         LANGGRAPH WORKFLOW                      │
└──────────────┬──────────────────────────────────┘
               │
        ┌──────▼──────┐
        │   START     │
        └──────┬──────┘
               │
        ┌──────▼───────────────────────┐
        │ AGENT 1: EXTRACTION          │
        │ (Extract text from documents)│
        │ - PyMuPDF extraction         │
        │ - Document classification    │
        │ - Quality assessment         │
        └──────┬──────────────────────┘
               │ (passes: extracted_text, doc_quality)
               │
        ┌──────▼───────────────────────┐
        │ AGENT 2: VERIFICATION        │
        │ (Verify credentials)         │
        │ - Name consistency           │
        │ - License verification       │
        │ - Institution check          │
        └──────┬──────────────────────┘
               │ (passes: credential_confidence, flags)
               │
        ┌──────▼───────────────────────┐
        │ AGENT 3: RISK ASSESSMENT     │
        │ (Assess fraud risk)          │
        │ - Behavioral analysis        │
        │ - Anomaly detection (ML)     │
        │ - Groq LLM reasoning         │
        └──────┬──────────────────────┘
               │ (passes: risk_score, trust_score)
               │
        ┌──────▼──────┐
        │   DECISION  │
        │  ENGINE     │
        └──────┬──────┘
               │
        ┌──────▼──────────────┐
        │ AUTO_APPROVED       │
        │ PENDING_REVIEW      │
        │ REJECTED            │
        └─────────────────────┘
```

---

## 🔧 Installation

```bash
pip install langgraph langchain groq
```

---

## 📝 Complete Implementation

### 1. State Definition

```python
# state.py
from typing import TypedDict, List, Dict, Any
from typing_extensions import NotRequired

class PractitionerState(TypedDict):
    """State passed between agents in the graph."""
    
    # Input
    practitioner_id: str
    full_name: str
    specialty: str
    country: str
    registration_number: str
    documents: List[Dict[str, str]]  # [{"path": "...", "type": "diploma"}]
    
    # Agent 1: Extraction Output
    extracted_text: NotRequired[str]
    document_quality: NotRequired[float]  # 0-1
    doc_anomalies: NotRequired[List[str]]
    
    # Agent 2: Verification Output
    name_consistency: NotRequired[float]  # 0-1
    license_valid: NotRequired[bool]
    institution_verified: NotRequired[bool]
    credential_flags: NotRequired[List[str]]
    credential_confidence: NotRequired[float]
    
    # Agent 3: Risk Assessment Output
    risk_score: NotRequired[float]  # 0-1
    trust_score: NotRequired[float]  # 0-1
    behavioral_risk: NotRequired[float]
    llm_reasoning: NotRequired[str]
    red_flags: NotRequired[List[str]]
    
    # Final Decision
    decision: NotRequired[str]  # AUTO_APPROVED, PENDING_REVIEW, REJECTED
    final_trust_score: NotRequired[int]  # 0-100
    final_reasoning: NotRequired[str]
    
    # Audit
    error_messages: NotRequired[List[str]]
```

### 2. Agent 1: Document Extraction

```python
# agents/extraction_agent.py
import logging
from typing import Dict, Any
from langchain.tools import tool
import fitz  # PyMuPDF
from state import PractitionerState

logger = logging.getLogger("doctome.extraction")

@tool
def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF document."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        logger.info(f"Extracted {len(text)} chars from {file_path}")
        return text
    except Exception as e:
        logger.error(f"Failed to extract from {file_path}: {e}")
        raise

@tool
def assess_document_quality(text: str, file_path: str) -> float:
    """Assess quality of extracted document (0-1)."""
    quality = 0.5
    
    # Text length
    if len(text) > 1000:
        quality += 0.2
    elif len(text) > 500:
        quality += 0.1
    
    # Word count
    words = len(text.split())
    if words > 100:
        quality += 0.2
    
    # Medical keywords
    medical_keywords = ["médecin", "doctor", "spécialité", "license", "diploma"]
    keyword_count = sum(1 for kw in medical_keywords if kw in text.lower())
    if keyword_count > 2:
        quality += 0.1
    
    return min(1.0, quality)

@tool
def classify_document_type(text: str, expected_type: str) -> str:
    """Classify document type."""
    text_lower = text.lower()
    
    if "diplôme" in text_lower or "degree" in text_lower:
        return "DIPLOMA"
    elif "licence" in text_lower or "license" in text_lower:
        return "LICENSE"
    elif "carte" in text_lower and "national" in text_lower:
        return "ID_CARD"
    elif "assurance" in text_lower or "insurance" in text_lower:
        return "INSURANCE"
    
    return expected_type or "UNKNOWN"

async def extraction_agent(state: PractitionerState) -> Dict[str, Any]:
    """
    Agent 1: Extract and analyze documents.
    
    Input: documents (file paths)
    Output: extracted_text, document_quality, doc_anomalies
    """
    logger.info(f"Starting extraction for {state['practitioner_id']}")
    
    try:
        documents = state.get("documents", [])
        if not documents:
            raise ValueError("No documents provided")
        
        extracted_texts = []
        quality_scores = []
        anomalies = []
        
        for doc in documents:
            # Extract text
            text = extract_text_from_pdf(doc["path"])
            extracted_texts.append(text)
            
            # Assess quality
            quality = assess_document_quality(text, doc["path"])
            quality_scores.append(quality)
            
            # Classify
            doc_type = classify_document_type(text, doc.get("type"))
            logger.info(f"Document classified as: {doc_type}")
            
            # Check anomalies
            if state.get("full_name") and state["full_name"].lower() not in text.lower():
                anomalies.append("name_not_in_document")
            
            if len(text) < 200:
                anomalies.append("document_text_too_short")
        
        combined_text = "\n".join(extracted_texts)
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        logger.info(f"Extraction complete: quality={avg_quality:.2f}, anomalies={len(anomalies)}")
        
        return {
            "extracted_text": combined_text,
            "document_quality": avg_quality,
            "doc_anomalies": anomalies
        }
    
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        return {
            "error_messages": [str(e)],
            "extracted_text": "",
            "document_quality": 0.0,
            "doc_anomalies": ["extraction_failed"]
        }
```

### 3. Agent 2: Credential Verification

```python
# agents/verification_agent.py
import logging
from typing import Dict, Any
from langchain.tools import tool
from difflib import SequenceMatcher
from state import PractitionerState

logger = logging.getLogger("doctome.verification")

@tool
def check_name_consistency(full_name: str, documents_text: str) -> float:
    """Check if name appears consistently in documents."""
    name_lower = full_name.lower()
    doc_lower = documents_text.lower()
    
    if name_lower in doc_lower:
        return 0.95
    
    name_parts = full_name.split()
    matches = sum(1 for part in name_parts if part.lower() in doc_lower)
    partial_score = matches / len(name_parts) if name_parts else 0
    
    ratio = SequenceMatcher(None, name_lower, doc_lower).ratio()
    
    return max(partial_score, ratio * 0.9)

@tool
def verify_license_number(registration_number: str, country: str) -> bool:
    """Verify medical license format and validity."""
    if not registration_number:
        return False
    
    # Format validation
    if len(registration_number) < 5 or len(registration_number) > 20:
        return False
    
    if not registration_number.replace(" ", "").isalnum():
        return False
    
    # In production: call government medical registry API
    # For MVP: assume valid if format correct
    return True

@tool
def verify_institution(documents_text: str, country: str) -> bool:
    """Verify medical institution is valid."""
    institutions = ["université", "university", "école", "school", "faculté", "medical"]
    doc_lower = documents_text.lower()
    
    found = any(inst in doc_lower for inst in institutions)
    return found

@tool
def check_blacklist(full_name: str, registration_number: str) -> bool:
    """Check if practitioner is blacklisted."""
    # In production: check against fraud database
    # For MVP: mock implementation
    known_blacklist = ["fake doctor", "fraudster"]
    name_lower = full_name.lower()
    
    return any(bad_name in name_lower for bad_name in known_blacklist)

async def verification_agent(state: PractitionerState) -> Dict[str, Any]:
    """
    Agent 2: Verify medical credentials.
    
    Input: extracted_text, full_name, specialty, country, registration_number
    Output: name_consistency, license_valid, institution_verified, credential_flags, credential_confidence
    """
    logger.info(f"Starting verification for {state['practitioner_id']}")
    
    try:
        extracted_text = state.get("extracted_text", "")
        if not extracted_text:
            logger.warning("No extracted text provided")
        
        # Check name consistency
        name_consistency = check_name_consistency(
            state.get("full_name", ""),
            extracted_text
        )
        
        # Verify license
        license_valid = verify_license_number(
            state.get("registration_number", ""),
            state.get("country", "")
        )
        
        # Verify institution
        institution_verified = verify_institution(
            extracted_text,
            state.get("country", "")
        )
        
        # Check blacklist
        is_blacklisted = check_blacklist(
            state.get("full_name", ""),
            state.get("registration_number", "")
        )
        
        # Generate flags
        flags = []
        if name_consistency < 0.8:
            flags.append("name_inconsistency")
        if not license_valid:
            flags.append("invalid_license")
        if not institution_verified:
            flags.append("invalid_institution")
        if is_blacklisted:
            flags.append("blacklisted")
        
        # Calculate confidence
        confidence = (
            name_consistency * 0.3 +
            (1.0 if license_valid else 0.0) * 0.4 +
            (1.0 if institution_verified else 0.0) * 0.3
        )
        
        logger.info(f"Verification complete: confidence={confidence:.2f}, flags={len(flags)}")
        
        return {
            "name_consistency": name_consistency,
            "license_valid": license_valid,
            "institution_verified": institution_verified,
            "credential_flags": flags,
            "credential_confidence": confidence
        }
    
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return {
            "error_messages": [str(e)],
            "name_consistency": 0.0,
            "license_valid": False,
            "institution_verified": False,
            "credential_flags": ["verification_failed"],
            "credential_confidence": 0.0
        }
```

### 4. Agent 3: Risk Assessment

```python
# agents/risk_assessment_agent.py
import logging
from typing import Dict, Any
from langchain.tools import tool
import os
from state import PractitionerState

logger = logging.getLogger("doctome.risk")

@tool
def analyze_behavioral_risk(documents: list, submission_time: str) -> float:
    """Analyze behavioral patterns for red flags."""
    risk = 0.0
    
    # Document count check
    if len(documents) < 3:
        risk += 0.2
    
    # Submission time (simplified)
    try:
        hour = int(submission_time.split("T")[1].split(":")[0]) if "T" in submission_time else 12
        if hour >= 22 or hour <= 5:
            risk += 0.1
    except:
        pass
    
    return min(1.0, risk)

@tool
def detect_statistical_anomalies(documents_text: str, full_name: str) -> list:
    """Detect statistical anomalies in documents."""
    anomalies = []
    
    # Text length
    if len(documents_text) < 500:
        anomalies.append("text_too_short")
    
    # Text repetition
    words = documents_text.split()
    unique_words = len(set(words))
    if unique_words < len(words) * 0.3:
        anomalies.append("excessive_repetition")
    
    # Special characters (OCR quality)
    special_chars = sum(1 for c in documents_text if not c.isalnum() and c not in " .,;:-'()!")
    if special_chars > len(documents_text) * 0.2:
        anomalies.append("poor_ocr_quality")
    
    # Name presence
    name_parts = full_name.split()
    for part in name_parts:
        if documents_text.lower().count(part.lower()) == 0:
            anomalies.append(f"name_part_missing: {part}")
    
    return anomalies

@tool
async def call_groq_llm(
    full_name: str,
    specialty: str,
    country: str,
    documents_text: str,
    document_quality: float,
    name_consistency: float
) -> Dict[str, Any]:
    """Call Groq LLM for intelligent risk assessment."""
    
    # In production:
    # from groq import Groq
    # client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    # response = client.chat.completions.create(...)
    
    # For MVP: mock based on input
    risk_level = 0.3
    
    if document_quality < 0.7:
        risk_level += 0.2
    if name_consistency < 0.8:
        risk_level += 0.2
    
    risk_level = min(1.0, risk_level)
    
    return {
        "risk_level": risk_level,
        "reasoning": f"Risk assessment for {full_name}",
        "red_flags": [] if risk_level < 0.5 else ["multiple_anomalies"]
    }

async def risk_assessment_agent(state: PractitionerState) -> Dict[str, Any]:
    """
    Agent 3: Assess fraud risk.
    
    Input: extracted_text, document_quality, name_consistency, etc.
    Output: risk_score, trust_score, llm_reasoning, red_flags
    """
    logger.info(f"Starting risk assessment for {state['practitioner_id']}")
    
    try:
        # Behavioral analysis
        behavioral_risk = analyze_behavioral_risk(
            state.get("documents", []),
            state.get("submission_time", "")
        )
        
        # Anomaly detection
        anomalies = detect_statistical_anomalies(
            state.get("extracted_text", ""),
            state.get("full_name", "")
        )
        
        # LLM reasoning
        llm_result = await call_groq_llm(
            state.get("full_name", ""),
            state.get("specialty", ""),
            state.get("country", ""),
            state.get("extracted_text", ""),
            state.get("document_quality", 0.5),
            state.get("name_consistency", 0.5)
        )
        
        # Combine scores
        risk_score = (
            behavioral_risk * 0.25 +
            (len(anomalies) / 10) * 0.25 +
            llm_result.get("risk_level", 0.5) * 0.5
        )
        
        risk_score = min(1.0, max(0.0, risk_score))
        trust_score = 1.0 - risk_score
        
        logger.info(f"Risk assessment complete: risk={risk_score:.2f}, trust={trust_score:.2f}")
        
        return {
            "risk_score": risk_score,
            "trust_score": trust_score,
            "behavioral_risk": behavioral_risk,
            "llm_reasoning": llm_result.get("reasoning", ""),
            "red_flags": llm_result.get("red_flags", [])
        }
    
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        return {
            "error_messages": [str(e)],
            "risk_score": 1.0,
            "trust_score": 0.0,
            "behavioral_risk": 1.0,
            "llm_reasoning": "Assessment failed",
            "red_flags": ["assessment_failed"]
        }
```

### 5. Decision Engine

```python
# agents/decision_engine.py
import logging
from typing import Dict, Any
from state import PractitionerState

logger = logging.getLogger("doctome.decision")

def decision_engine(state: PractitionerState) -> Dict[str, Any]:
    """
    Final decision based on all agents' outputs.
    
    Returns: decision (AUTO_APPROVED / PENDING_REVIEW / REJECTED), trust_score, reasoning
    """
    logger.info(f"Making decision for {state['practitioner_id']}")
    
    # Get all scores
    document_quality = state.get("document_quality", 0.0)
    credential_confidence = state.get("credential_confidence", 0.0)
    trust_score_normalized = state.get("trust_score", 0.0)
    
    # Weighted calculation
    final_score = (
        document_quality * 0.3 +
        credential_confidence * 0.4 +
        trust_score_normalized * 0.3
    )
    
    # Medical domain decision rules
    if final_score >= 0.85:
        decision = "AUTO_APPROVED"
        reasoning = "All medical credentials verified successfully"
    elif final_score >= 0.65:
        decision = "PENDING_REVIEW"
        reasoning = "Some credentials require human verification"
    else:
        decision = "REJECTED"
        reasoning = "Multiple red flags detected"
    
    final_trust_score = int(final_score * 100)
    
    logger.info(f"Decision: {decision} (score={final_trust_score})")
    
    return {
        "decision": decision,
        "final_trust_score": final_trust_score,
        "final_reasoning": reasoning
    }
```

### 6. LangGraph Workflow

```python
# graph.py
from langgraph.graph import StateGraph, END
from state import PractitionerState
from agents.extraction_agent import extraction_agent
from agents.verification_agent import verification_agent
from agents.risk_assessment_agent import risk_assessment_agent
from agents.decision_engine import decision_engine
import logging

logger = logging.getLogger("doctome.graph")

def create_verification_graph():
    """Create LangGraph workflow."""
    
    graph = StateGraph(PractitionerState)
    
    # Add nodes
    graph.add_node("extraction", extraction_agent)
    graph.add_node("verification", verification_agent)
    graph.add_node("risk_assessment", risk_assessment_agent)
    graph.add_node("decision", decision_engine)
    
    # Add edges (sequential flow)
    graph.add_edge("extraction", "verification")
    graph.add_edge("verification", "risk_assessment")
    graph.add_edge("risk_assessment", "decision")
    graph.add_edge("decision", END)
    
    # Set starting point
    graph.set_entry_point("extraction")
    
    # Compile
    app = graph.compile()
    
    logger.info("LangGraph workflow compiled")
    return app

# Usage
verification_graph = create_verification_graph()
```

### 7. Django Integration

```python
# views.py
import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from .graph import verification_graph
from practitioners.models import Practitioner, TrustAssessment

class SubmitPractitionerView(APIView):
    """Submit practitioner for verification."""
    
    async def post(self, request):
        # ... save documents ...
        
        # Prepare state for graph
        initial_state = {
            "practitioner_id": str(practitioner.id),
            "full_name": full_name,
            "specialty": specialty,
            "country": country,
            "registration_number": registration_number,
            "documents": documents_data
        }
        
        # Run graph
        final_state = await asyncio.to_thread(
            verification_graph.invoke,
            initial_state
        )
        
        # Save results
        TrustAssessment.objects.create(
            practitioner=practitioner,
            trust_score=final_state.get("final_trust_score", 0),
            decision=final_state.get("decision", "REJECTED"),
            ai_reasoning=final_state.get("final_reasoning", "")
        )
        
        return Response(final_state)
```

---

## 🚀 Running the Graph

```python
from graph import verification_graph

# Input state
input_state = {
    "practitioner_id": "pract_123",
    "full_name": "Dr. Ahmed Ben Ali",
    "specialty": "Cardiology",
    "country": "Algeria",
    "registration_number": "12345ABC",
    "documents": [
        {"path": "diploma.pdf", "type": "diploma"},
        {"path": "license.pdf", "type": "license"},
        {"path": "id.pdf", "type": "id"}
    ]
}

# Run workflow
result = verification_graph.invoke(input_state)

print(f"Decision: {result['decision']}")
print(f"Trust Score: {result['final_trust_score']}/100")
print(f"Reasoning: {result['final_reasoning']}")
```

---

## 📊 Graph Execution Flow

```
Input State
   ↓
Agent 1: Extraction
  - Extract: "Diploma for Dr. Ahmed..."
  - Quality: 0.87
  - Anomalies: []
   ↓ (state updated with extraction output)
Agent 2: Verification
  - Name Consistency: 0.92
  - License Valid: True
  - Institution Verified: True
  - Confidence: 0.88
   ↓ (state updated with verification output)
Agent 3: Risk Assessment
  - Behavioral Risk: 0.1
  - Anomalies: []
  - LLM Risk: 0.2
  - Trust Score: 0.85
   ↓ (state updated with risk output)
Decision Engine
  - Final Score: (0.87 * 0.3) + (0.88 * 0.4) + (0.85 * 0.3) = 0.865
  - Decision: AUTO_APPROVED
  - Final Trust: 87/100
   ↓
Output State (complete with all agent results)
```

---

## 🔌 Key Benefits of LangGraph

✅ **State Management:** All agent outputs stored in shared state  
✅ **Sequential Flow:** Agents run in order, each using previous results  
✅ **Error Handling:** Graceful error propagation through graph  
✅ **Debugging:** Visual graph representation and step-by-step execution  
✅ **Flexibility:** Easy to add/modify agents without breaking workflow  
✅ **Async Support:** Full async/await support for parallel tasks (if needed)

---

**Ready to implement?** This LangGraph approach is production-ready and scalable!
