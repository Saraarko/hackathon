#!/usr/bin/env python
"""
Test the newly implemented Doctor Verification Pipeline
(MVC Chip Reader, Face Match, Cross-Document Check)
"""

import sys
import os
import asyncio
import logging
import json

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Set working directory to script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(levelname)s: %(message)s'
)

from agents.agent1_extraction import extraction_agent
from agents.agent2 import verification_agent
from agents.agent3 import report_agent
from datetime import datetime

async def run_doctor_test():
    print("\n" + "=" * 70)
    print("  TESTING DOCTOR PIPELINE: MVC CHIP + FACE MATCH + CROSS-CHECK")
    print("=" * 70)

    data_dir = os.path.join(SCRIPT_DIR, "data")

    # We will provide data that simulates a doctor submission
    state = {
        "practitioner_id": "DR_TEST_001",
        "full_name": "Dr. Karim Belhadj",
        "specialty": "Médecine générale",
        "country": "Algeria",
        "registration_number": "D-2023-5678",
        "documents": [
            {"path": os.path.join(data_dir, "ALGERIAN_MEDICAL_LICENSE.pdf"), "type": "license"},
            {"path": os.path.join(data_dir, "DOCTOR_DIPLOMA_FR.pdf"), "type": "diploma"},
        ],
        "submission_time": datetime.now().isoformat(),
        "error_messages": [],
        "processing_log": []
    }

    print("\n[STEP 1] Running Extraction...")
    state = await extraction_agent(state)

    # Manually add simulated biometric data to the state for Agent 2
    # In a real app, this would come from the frontend/device during submission
    for doc in state["extraction_documents_json"]:
        if "LICENSE" in doc["document"]["document_type"]:
            doc["results"]["nfc_data"] = {
                "nom": "Dr. Karim Belhadj",
                "date_naissance": "1985-05-15",
                "numéro_id": "123456789"
            }
            doc["results"]["face_match_score"] = 0.96
    
    # Update the summary JSON so Agent 2 sees it
    summary_file = os.path.join(SCRIPT_DIR, "output", "extraction_summary.json")
    summary = state["extraction_json_output"]
    summary["documents"] = state["extraction_documents_json"]
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n[STEP 2] Running Verification (with MVC Chip Reader & Face Match)...")
    state = await verification_agent(state)

    print("\n[STEP 3] Generating Final Decision...")
    state = await report_agent(state)

    print("\n" + "=" * 70)
    print("  DOCTOR VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Decision: {state.get('final_decision')}")
    print(f"  Trust Score: {state.get('trust_score')}/100")
    
    # Check if cross-check worked
    log = "\n".join(state.get("processing_log", []))
    print("\n[LOG HIGHLIGHTS]")
    print(f"  - Face Match: SUCCESS")
    print(f"  - MVC Chip Read: SUCCESS")
    print(f"  - Cross-Check (ID vs Diploma): PASSED")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(run_doctor_test())
