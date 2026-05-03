#!/usr/bin/env python
"""Production runner for Agent 1 + Agent 2 LangGraph workflow on real data"""

import asyncio
import logging
from graph import run_verification_workflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run():
    """Run workflow on all real documents"""

    print("\n" + "="*70)
    print("DOCTOME - Medical Credential Verification (Agent 1 + Agent 2)")
    print("="*70 + "\n")

    result = await run_verification_workflow(
        practitioner_id='doctor_001',
        full_name='Dr. Ahmed Ben Ali',
        specialty='Cardiology',
        country='Algeria',
        registration_number='12345ABC',
        documents=[
            {'path': 'data/DOCTOR_DIPLOMA_FR.pdf', 'type': 'diploma'},
            {'path': 'data/ALGERIAN_MEDICAL_LICENSE.pdf', 'type': 'license'},
            {'path': 'data/HOSPITAL_LICENSE.pdf', 'type': 'license'},
            {'path': 'data/LABORATORY_ACCREDITATION.pdf', 'type': 'certification'},
            {'path': 'data/doctor_credential_test.pdf', 'type': 'diploma'},
            {'path': 'data/CHEIKHAOUI_AHMED_MAHDI_credential.pdf', 'type': 'diploma'},
            {'path': 'data/certificat_iso.jpg', 'type': 'certificate'},
        ]
    )

    print("\n" + "="*70)
    print("WORKFLOW RESULTS")
    print("="*70)

    # Agent 1 Results
    extraction_data = result.get('extraction_json_output', {})
    if extraction_data:
        total_docs = extraction_data.get('summary', {}).get('total_documents', 0)
        avg_quality = extraction_data.get('summary', {}).get('average_quality', 0)
        print(f"\n[AGENT 1 - EXTRACTION]")
        print(f"  Total Documents: {total_docs}")
        print(f"  Average Quality: {avg_quality}")

    # Agent 2 Results
    verification_data = result.get('verification_json_output', {})
    if verification_data:
        trust_score = result.get('trust_score', 'N/A')
        print(f"\n[AGENT 2 - VERIFICATION]")
        print(f"  Final Trust Score: {trust_score}/100")

        flags = verification_data.get('issues_found', [])
        if flags:
            print(f"  Issues Found: {len(flags)}")
            for flag in flags[:5]:  # Show first 5
                print(f"    - {flag}")

    # Agent 3 Results
    report_data = result.get('report_json_output', {})
    if report_data:
        print(f"\n[AGENT 3 - REPORTING & DECISION]")
        overall_decision = report_data.get('overall_decision', {})
        print(f"  Final Decision: {overall_decision.get('status', 'N/A')}")
        print(f"  Decision Type: {overall_decision.get('type', 'N/A')}")
        print(f"  Priority: {overall_decision.get('priority', 'N/A')}")
        print(f"  Reasoning: {overall_decision.get('reasoning', 'N/A')}")
        print(f"  Human Review Required: {overall_decision.get('requires_human_review', False)}")

    errors = result.get('error_messages', [])
    if errors:
        print(f"\n[ERRORS]")
        for error in errors:
            print(f"  - {error}")

    print("\n" + "="*70)
    print("OUTPUT FILES SAVED TO: output/")
    print("="*70)
    print("  - extraction_summary.json")
    print("  - *_extraction.json (one per document)")
    print("  - verification_summary.json")
    print("  - *_verification.json (one per document)")
    print("  - final_report_summary.json")
    print("  - *_final_report.json (one per document)")
    print("="*70)
    print("EMAIL: Summary report sent to sarahriehe@gmail.com")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(run())
