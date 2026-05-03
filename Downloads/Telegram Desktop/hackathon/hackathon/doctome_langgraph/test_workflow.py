#!/usr/bin/env python
"""Test Agent 1 + Agent 2 workflow via LangGraph"""

import asyncio
import logging
from graph import run_verification_workflow

logging.basicConfig(level=logging.INFO)

async def test():
    result = await run_verification_workflow(
        practitioner_id='pract_001',
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

    print('\n' + '='*60)
    print('AGENT 1 + AGENT 2 WORKFLOW COMPLETE')
    print('='*60)

    extraction_data = result.get('extraction_json_output', {})
    if extraction_data:
        total_docs = extraction_data.get('summary', {}).get('total_documents', 0)
        print(f'[OK] Extracted Documents: {total_docs}')

    trust_score = result.get('trust_score', 'N/A')
    print(f'[OK] Verification Trust Score: {trust_score}/100')

    flags = result.get('credential_flags', [])
    if flags:
        print(f'[OK] Credential Flags: {len(flags)} issues detected')
    else:
        print(f'[OK] Credential Flags: None')

    errors = result.get('error_messages', [])
    if errors:
        print(f'[ERROR] Issues: {errors}')

    print('='*60)
    print()

asyncio.run(test())
