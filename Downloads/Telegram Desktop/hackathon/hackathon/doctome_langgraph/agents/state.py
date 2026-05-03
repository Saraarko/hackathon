"""
State Definition for LangGraph Workflow
Shared state passed between all agents
"""

from typing import TypedDict, List, Dict, Any, Optional

class PractitionerState(TypedDict):
    """
    State schema for the medical verification workflow.
    Each agent reads from this state and updates it with results.
    """

    # ==================== INPUT DATA ====================
    practitioner_id: str
    full_name: str
    specialty: str
    country: str
    registration_number: str
    documents: List[Dict[str, str]]  # [{"path": "...", "type": "diploma"}]
    submission_time: Optional[str]  # ISO format

    # ==================== AGENT 1: EXTRACTION OUTPUT ====================
    extracted_text: Optional[str]  # Combined text from all documents
    document_quality: Optional[float]  # 0.0-1.0
    doc_anomalies: Optional[List[str]]  # List of detected anomalies
    document_count: Optional[int]

    # ==================== AGENT 2: VERIFICATION OUTPUT ====================
    name_consistency: Optional[float]  # 0.0-1.0
    license_valid: Optional[bool]
    institution_verified: Optional[bool]
    credential_flags: Optional[List[str]]
    credential_confidence: Optional[float]  # 0.0-1.0
    is_blacklisted: Optional[bool]

    # ==================== AGENT 3: RISK ASSESSMENT OUTPUT ====================
    risk_score: Optional[float]  # 0.0-1.0 (higher = more risky)
    trust_score: Optional[float]  # 0.0-1.0 (inverse of risk)
    behavioral_risk: Optional[float]  # 0.0-1.0
    anomalies_detected: Optional[List[str]]
    llm_reasoning: Optional[str]
    red_flags: Optional[List[str]]

    # ==================== DECISION OUTPUT ====================
    decision: Optional[str]  # AUTO_APPROVED, PENDING_REVIEW, REJECTED
    final_trust_score: Optional[int]  # 0-100
    final_reasoning: Optional[str]

    # ==================== JSON OUTPUTS (for API responses) ====================
    extraction_json_output: Optional[Dict[str, Any]]  # Agent 1 summary JSON response
    extraction_documents_json: Optional[List[Dict[str, Any]]]  # Individual JSON for each document
    verification_json_output: Optional[Dict[str, Any]]  # Agent 2 JSON response
    risk_assessment_json_output: Optional[Dict[str, Any]]  # Agent 3 JSON response

    # ==================== AUDIT ====================
    error_messages: Optional[List[str]]
    processing_log: Optional[List[str]]
