"""Test verification on ISO certificate image only"""

import asyncio
import json
import logging
from graph import run_verification_workflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_iso_only():
    """Test only certificat_iso.jpg"""

    print("\n" + "="*70)
    print("TESTING ISO CERTIFICATE ONLY (certificat_iso.jpg)")
    print("="*70 + "\n")

    result = await run_verification_workflow(
        practitioner_id='lab_001',
        full_name='Laboratory ISO Certification',
        specialty='Laboratory Services',
        country='Algeria',
        registration_number='ISO-2023-001',
        documents=[
            {'path': 'data/certificat_iso.jpg', 'type': 'certificate'}
        ]
    )

    print("\n" + "="*70)
    print("EXTRACTION RESULTS (AGENT 1)")
    print("="*70)

    extraction = result.get('extraction_json_output', {})
    if extraction:
        documents = extraction.get('documents', [])
        if documents:
            doc = documents[0]
            print(f"Document: {doc.get('file_path')}")
            print(f"Entity Type: {doc.get('metadata', {}).get('entity_type')}")
            print(f"Quality Score: {doc.get('results', {}).get('document_quality', 0)}")
            print(f"\nExtracted Text Preview:")
            text = doc.get('results', {}).get('extracted_text', '')
            print(text[:500] + "..." if len(text) > 500 else text)

    print("\n" + "="*70)
    print("VERIFICATION RESULTS (AGENT 2)")
    print("="*70)

    verification = result.get('verification_json_output', {})
    if verification:
        trust_score = result.get('trust_score', 0)
        docs_verified = verification.get('documents_verified', [])

        if docs_verified:
            doc_result = docs_verified[0]
            print(f"Document: {doc_result.get('document')}")
            print(f"Entity Type: {doc_result.get('entity_type')}")
            print(f"Trust Score: {doc_result.get('scoring_details', {}).get('final_average_score')}/100")
            print(f"\nIssues Found:")
            for issue in doc_result.get('issues_found', []):
                print(f"  - {issue}")
            print(f"\nAnalysis: {doc_result.get('analysis_summary')}")

    print("\n" + "="*70)
    print("FINAL DECISION (AGENT 3)")
    print("="*70)

    report = result.get('report_json_output', {})
    if report:
        decision = report.get('overall_decision', {})
        print(f"Decision: {decision.get('status')}")
        print(f"Trust Score: {report.get('overall_scoring', {}).get('average_trust_score')}/100")
        print(f"Reasoning: {decision.get('reasoning')}")

    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(test_iso_only())
