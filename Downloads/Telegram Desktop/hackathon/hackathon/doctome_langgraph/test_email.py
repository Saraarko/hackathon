#!/usr/bin/env python
"""Test email sending from Agent 3"""

import asyncio
import json
import os
from agents.agent3 import send_report_email

# Sample report
test_report = {
    "practitioner": {
        "full_name": "Dr. Ahmed Ben Ali",
        "specialty": "Cardiology"
    },
    "decision": {
        "status": "PENDING_REVIEW",
        "reasoning": "Requires human verification"
    },
    "overall_scoring": {
        "average_trust_score": 72.5
    },
    "timestamp": "2026-05-02T14:00:00Z"
}

# Create test report file
test_report_path = "output/test_email_report.json"
os.makedirs("output", exist_ok=True)
with open(test_report_path, 'w') as f:
    json.dump(test_report, f, indent=2)

# Test sending
print("Testing email send...")
print(f"Report file: {test_report_path}")
print(f"Recipient: sarahriehe@gmail.com\n")

success = send_report_email(test_report, test_report_path, "sarahriehe@gmail.com")

if success:
    print("[SUCCESS] Email sent successfully to sarahriehe@gmail.com!")
    print("\nThe workflow can now send reports via email after each verification.")
else:
    print("[FAILED] Email not sent")
    print("\n[NEXT STEPS - Fix SendGrid Sender Authentication]")
    print("1. Login to SendGrid Dashboard: https://app.sendgrid.com")
    print("2. Go to: Settings > Sender Authentication")
    print("3. Click 'Verify a Single Sender'")
    print("4. Enter: sarahriehe@gmail.com")
    print("5. Click 'Create'")
    print("6. Check email for verification link")
    print("7. Click the link to verify")
    print("8. Run this test again")
    print("\nOnce verified, Agent 3 will send reports automatically!")
