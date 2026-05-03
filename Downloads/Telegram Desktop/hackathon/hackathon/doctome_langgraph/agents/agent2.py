"""
Agent 2: Credential Verification Agent (Hybrid Scoring)
------------------------------------------------------
1. Reads JSON from Agent 1.
2. Structural Score: Compares extracted JSON against a "Gold Standard" Library.
3. Semantic Score: Uses Groq LLM to analyze content and logic.
4. Final Score: Calculates the Average (Structural + Semantic) / 2.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, List

import sys
# Add parent directory to path to allow importing state.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from state import PractitionerState
except ImportError:
    # Fallback for package execution
    try:
        from .state import PractitionerState
    except ImportError:
        # Define a placeholder if all imports fail (for standalone linting)
        PractitionerState = Any

try:
    from qr_verifier import QRVerifier
except ImportError:
    try:
        from .qr_verifier import QRVerifier
    except ImportError:
        QRVerifier = None

try:
    from verification_pipeline import DoctorVerification, ClinicVerification, LabVerification
except ImportError:
    try:
        from .verification_pipeline import DoctorVerification, ClinicVerification, LabVerification
    except ImportError:
        DoctorVerification = ClinicVerification = LabVerification = None

from dotenv import load_dotenv

# Load .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger("doctome.verification")

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS_DIR = os.path.join(BASE_DIR, "agents", "schemas")
SUMMARY_JSON_PATH = os.path.join(BASE_DIR, "output", "extraction_summary.json")

OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Mapping document types to schema files
SCHEMA_MAP = {
    "medecin_individuel": "doctor_license.json",
    "clinique_hopital": "clinic_operating_license.json",
    "laboratoire": "lab_accreditation.json"
}

# ─────────────────────────────────────────────
# STEP 0: SPECIALIZED VERIFICATION PIPELINES
# ─────────────────────────────────────────────

def verify_with_pipeline(extracted_data: Dict[str, Any], entity_type: str, all_docs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Use specialized pipelines for doctors, clinics, labs"""
    try:
        if entity_type == "medecin_individuel" and DoctorVerification:
            result = DoctorVerification.calculate_doctor_score(extracted_data, all_docs)
            logger.info(f"[AGENT 2] Doctor pipeline: {result['final_score']}/100")
            return result
        elif entity_type == "clinique_hopital" and ClinicVerification:
            result = ClinicVerification.calculate_clinic_score(extracted_data, all_docs)
            logger.info(f"[AGENT 2] Clinic pipeline: {result['final_score']}/100")
            return result
        elif entity_type == "laboratoire" and LabVerification:
            result = LabVerification.calculate_lab_score(extracted_data, all_docs)
            logger.info(f"[AGENT 2] Lab pipeline: {result['final_score']}/100")
            return result
        return None
    except Exception as e:
        logger.error(f"[AGENT 2] Pipeline error: {str(e)}")
        return None

# ─────────────────────────────────────────────
# STEP 1: LIBRARY COMPARISON (STRUCTURAL)
# ─────────────────────────────────────────────

def calculate_structural_score(extracted_data: Dict[str, Any], entity_type: str) -> Tuple[float, List[str]]:
    """
    Compare extracted data against the Gold Standard JSON Library.
    Returns (Score 0-100, Issues List).
    """
    schema_file = SCHEMA_MAP.get(entity_type)
    if not schema_file:
        return 50.0, ["Unknown entity type: No schema found for comparison."]

    schema_path = os.path.join(SCHEMAS_DIR, schema_file)
    if not os.path.exists(schema_path):
        return 50.0, [f"Schema file {schema_file} missing from library."]

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    required_fields = schema.get("required_fields", [])
    weights = schema.get("weights", {})
    field_rules = schema.get("field_rules", {})

    earned_points = 0.0
    total_points = 100.0
    issues = []

    # Check each required field
    for field in required_fields:
        weight = weights.get(field, 0.1) * 100
        value = extracted_data.get(field)

        if not value or str(value).strip() == "" or "not found" in str(value).lower():
            issues.append(f"Missing mandatory field: {field}")
            continue

        # Basic rule validation if exists
        rule = field_rules.get(field)
        field_valid = True
        if rule:
            if rule.get("type") == "string":
                if rule.get("min_length") and len(str(value)) < rule["min_length"]:
                    field_valid = False
                    issues.append(f"Field {field} is too short.")
                if rule.get("pattern") and not re.match(rule["pattern"], str(value)):
                    field_valid = False
                    issues.append(f"Field {field} does not match required format.")

        if field_valid:
            earned_points += weight
        else:
            issues.append(f"Invalid format for field: {field}")

    return round(min(earned_points, 100.0), 2), issues

# ─────────────────────────────────────────────
# STEP 2: GROQ LLM ANALYSIS (SEMANTIC)
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a medical compliance auditor.
Your job is to analyze extracted document data and provide a Trust Score (0-100).
Focus on logic, consistency, and professional legitimacy.
Ignore minor OCR typos, but flag missing critical info or suspicious patterns.
Return ONLY valid JSON."""

def call_groq(extracted_json: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
    """Call Groq API (llama-3.1-8b-instant) for semantic analysis."""
    if not GROQ_AVAILABLE:
        logger.warning("Groq not available. Install: pip install groq")
        return {
            "semantic_score": 50,
            "analysis": "Groq API not available",
            "red_flags": ["API not configured"]
        }

    if not GROQ_API_KEY:
        logger.warning("[GROQ] No API key found")
        return {
            "semantic_score": 50,
            "analysis": "Groq API key not configured",
            "red_flags": ["No API key"]
        }

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""You are a medical compliance auditor. Analyze this {entity_type} extraction data and return ONLY valid JSON (no markdown, no extra text):

Extracted Data:
{json.dumps(extracted_json, indent=2)}

Tasks:
1. Assess the quality of information.
2. Check if the data is consistent (e.g. name matches across fields).
3. Provide a 'semantic_score' from 0 to 100.

Return ONLY this JSON format (no markdown code blocks):
{{
  "semantic_score": <int 0-100>,
  "analysis": "<short summary of analysis>",
  "red_flags": ["list of potential issues or concerns"]
}}"""

    try:
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = message.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        result = json.loads(response_text.strip())
        logger.info(f"[GROQ] Semantic score for {entity_type}: {result.get('semantic_score', 'N/A')}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq response as JSON: {str(e)}")
        return {
            "semantic_score": 50,
            "analysis": "Analysis inconclusive due to response format issue",
            "red_flags": ["Response parsing failed"]
        }
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        return {
            "semantic_score": 50,
            "analysis": f"API error: {str(e)}",
            "red_flags": ["API call failed"]
        }

# ─────────────────────────────────────────────
# MAIN AGENT
# ─────────────────────────────────────────────

async def verification_agent(state: PractitionerState) -> PractitionerState:
    logger.info("[AGENT 2] Starting Hybrid Verification for ALL documents...")

    try:
        # 1. Load Agent 1 Data
        if not os.path.exists(SUMMARY_JSON_PATH):
            raise FileNotFoundError(f"Agent 1 summary not found at {SUMMARY_JSON_PATH}")

        with open(SUMMARY_JSON_PATH, 'r', encoding='utf-8') as f:
            agent1_data = json.load(f)

        # Process ALL documents
        documents = agent1_data.get("documents", [])
        all_results = []
        all_flags = []

        # Group documents by entity_type
        documents_by_type = {}
        scores_by_type = {}

        logger.info(f"[AGENT 2] Processing {len(documents)} documents...")

        for doc_index, document in enumerate(documents):
            logger.info(f"[AGENT 2] Verifying document {doc_index + 1}/{len(documents)}")

            # Get entity_type and extracted data
            entity_type = document.get("metadata", {}).get("entity_type", "UNKNOWN")
            extracted_data = document.get("results", {})
            doc_path = document.get("document", {}).get("file_path", f"document_{doc_index}")

            # Get filename without extension for output
            doc_name = os.path.splitext(os.path.basename(doc_path))[0]

            # Try specialized verification pipeline first (Phases 1-4)
            pipeline_result = verify_with_pipeline(extracted_data, entity_type, documents)

            if pipeline_result:
                # Use pipeline result
                final_trust_score = pipeline_result["final_score"]
                pipeline_details = pipeline_result.get("scores", {})
                structural_issues = [v.get("message", "") for v in pipeline_details.values() if not v.get("pass")]
                llm_result = {"red_flags": [], "analysis": f"Verified via {entity_type} pipeline"}
                logger.info(f"[AGENT 2] Using {entity_type} pipeline verification")
            else:
                # 2. Fallback: Structural Score (Library Comparison)
                structural_score, structural_issues = calculate_structural_score(extracted_data, entity_type)

                # 3. Fallback: Semantic Score (Groq LLM - llama-3.1-8b-instant)
                llm_result = call_groq(extracted_data, entity_type)
                semantic_score = llm_result.get("semantic_score", 50)

                # 4. Final Average (La Moyenne)
                final_trust_score = round((structural_score + semantic_score) / 2, 2)
                logger.info(f"[AGENT 2] Using hybrid verification (structural+semantic)")

            logger.info(f"[AGENT 2] Document {doc_index + 1}: Final={final_trust_score}")

            # 5. Build Result for this document
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "document": doc_path,
                "entity_type": entity_type,
                "scoring_details": {
                    "final_average_score": final_trust_score
                },
                "issues_found": structural_issues + llm_result.get("red_flags", []),
                "analysis_summary": llm_result.get("analysis", "")
            }

            # Save individual verification JSON
            output_file = os.path.join(OUTPUT_FOLDER, f"{doc_name}_verification.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"[AGENT 2] Saved verification: {output_file}")

            # Collect results
            all_results.append(result)
            all_flags.extend(structural_issues + llm_result.get("red_flags", []))

            # Group by entity type for category scoring
            if entity_type not in documents_by_type:
                documents_by_type[entity_type] = []
                scores_by_type[entity_type] = []
            documents_by_type[entity_type].append(result)
            scores_by_type[entity_type].append(final_trust_score)

        # Calculate category averages
        category_scores = {}
        for entity_type, scores in scores_by_type.items():
            avg_score = round(sum(scores) / len(scores), 2) if scores else 0
            category_scores[entity_type] = avg_score
            logger.info(f"[AGENT 2] Category '{entity_type}': {avg_score}/100 (from {len(scores)} documents)")

        # Calculate overall average trust score from category averages
        if category_scores:
            average_trust_score = round(sum(category_scores.values()) / len(category_scores), 2)
        else:
            average_trust_score = 0

        # Create summary verification result with category breakdown
        summary_result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_documents_verified": len(documents),
            "scoring": {
                "category_scores": category_scores,
                "average_trust_score": average_trust_score
            },
            "category_breakdown": {
                entity_type: {
                    "count": len(documents_by_type[entity_type]),
                    "average_score": category_scores[entity_type],
                    "documents": documents_by_type[entity_type]
                }
                for entity_type in documents_by_type.keys()
            },
            "documents_verified": all_results,
            "all_issues_found": list(set(all_flags)),  # Unique issues
            "total_issues": len(set(all_flags))
        }

        # Save summary verification JSON
        summary_file = os.path.join(OUTPUT_FOLDER, "verification_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, indent=2, ensure_ascii=False)

        logger.info(f"[AGENT 2] Verification summary saved: {summary_file}")
        logger.info(f"[AGENT 2] Average Trust Score across all documents: {average_trust_score}/100")

        # Update State with summary
        state["trust_score"] = average_trust_score
        state["verification_json_output"] = summary_result
        state["credential_flags"] = list(set(all_flags))

        return state

    except Exception as e:
        logger.error(f"[AGENT 2] Error: {str(e)}")
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Agent 2 Error: {str(e)}")
        return state

if __name__ == "__main__":
    import asyncio
    
    # Configure logging for test
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    async def test():
        print("\n" + "="*50)
        print("TESTING AGENT 2: HYBRID VERIFICATION")
        print("="*50)
        
        # Initial state
        test_state = {
            "practitioner_id": "test_001",
            "error_messages": [],
            "processing_log": []
        }
        
        # Run agent
        result_state = await verification_agent(test_state)
        
        # Print results
        print("\n[SCORING RESULTS]")
        details = result_state.get("verification_json_output", {}).get("scoring_details", {})
        print(f"Structural Score: {details.get('structural_score')}/100")
        print(f"Semantic Score:   {details.get('semantic_score')}/100")
        print(f"FINAL AVERAGE:    {result_state.get('trust_score')}/100")
        
        print("\n[ISSUES FOUND]")
        for issue in result_state.get("credential_flags", []):
            print(f"- {issue}")
            
        print("\n" + "="*50 + "\n")

    asyncio.run(test())
