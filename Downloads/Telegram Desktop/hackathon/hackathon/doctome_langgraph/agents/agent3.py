"""
Agent 3: Report Generator & Decision Engine
---------------------------------------------
1. Takes trust_score from Agent 2
2. Decision Logic:
   - Score > 85: AUTO_APPROVED
   - Score < 50: AUTO_REJECTED
   - 50-85: PENDING_HUMAN_REVIEW (needs verification humaine)
3. Generates comprehensive report with all data and decision
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, List

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from state import PractitionerState
except ImportError:
    try:
        from .state import PractitionerState
    except ImportError:
        PractitionerState = Any

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger("doctome.report")

# ─────────────────────────────────────────────
# SENDGRID EMAIL SETUP (REST API)
# ─────────────────────────────────────────────

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

try:
    import requests
    import base64
    from fpdf import FPDF
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# ─────────────────────────────────────────────
# GROQ LLM SETUP
# ─────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Decision thresholds
APPROVED_THRESHOLD = 85
REJECTED_THRESHOLD = 50

# ─────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────

def _get_recommendations(decision_status: str, trust_score: float) -> List[str]:
    """Generate recommendations based on decision."""
    if decision_status == "APPROVED":
        return [
            "Credentials verified successfully - proceed with onboarding",
            "Add practitioner to trusted registry",
            "Issue approval certificate",
            "Schedule orientation meeting",
            "No further verification required"
        ]
    elif decision_status == "REJECTED":
        return [
            "Request additional documentation from practitioner",
            "Conduct manual verification of submitted documents",
            "Contact issuing institutions for verification",
            "Document findings in compliance system",
            "Contact practitioner with decision and appeal options"
        ]
    else:  # PENDING_REVIEW
        return [
            "Assign to compliance officer for manual review",
            "Schedule verification meeting with practitioner",
            "Request clarification on flagged inconsistencies",
            "Verify documents with issuing institutions",
            "Provide decision within 5 business days"
        ]

def generate_pdf_report(report: Dict[str, Any], output_path: str) -> bool:
    """Generate professional PDF report from verification results."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=15)

        # Color scheme
        header_color = (44, 62, 80)      # Dark blue-grey
        section_color = (52, 152, 219)   # Blue
        approved_color = (46, 204, 113)  # Green
        rejected_color = (231, 76, 60)   # Red
        pending_color = (241, 196, 15)   # Orange

        # Title
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 12, "MEDICAL CREDENTIAL VERIFICATION REPORT", ln=True, align="C")

        # Separator line
        pdf.set_draw_color(52, 152, 219)
        pdf.set_line_width(1)
        pdf.line(15, pdf.get_y() + 2, 195, pdf.get_y() + 2)
        pdf.ln(5)

        # Practitioner Information Section
        practitioner = report.get("practitioner", {})
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, "PRACTITIONER INFORMATION", ln=True)
        pdf.set_line_width(0.5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(45, 7, "Name:", border=0)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, practitioner.get('full_name', 'N/A'), ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.cell(45, 7, "Specialty:", border=0)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, practitioner.get('specialty', 'N/A'), ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.cell(45, 7, "Registration:", border=0)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, practitioner.get('registration_number', 'N/A'), ln=True)
        pdf.ln(3)

        # Verification Results Section
        scoring = report.get("overall_scoring", {})
        trust_score = scoring.get("average_trust_score", 0)

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, "VERIFICATION RESULTS", ln=True)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(45, 7, "Trust Score:", border=0)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(52, 152, 219)
        pdf.cell(0, 7, f"{trust_score}/100", ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(45, 7, "Documents Reviewed:", border=0)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 7, str(scoring.get('total_documents', 0)), ln=True)
        pdf.ln(3)

        # Decision Section
        decision = report.get("overall_decision", {})
        decision_status = decision.get('status', 'UNKNOWN')

        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, "DECISION", ln=True)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

        # Status box
        if decision_status == "APPROVED":
            pdf.set_fill_color(46, 204, 113)
        elif decision_status == "REJECTED":
            pdf.set_fill_color(231, 76, 60)
        else:
            pdf.set_fill_color(241, 196, 15)

        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, f"  {decision_status}  ", ln=True, fill=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 11)
        pdf.ln(2)
        pdf.multi_cell(0, 5, f"Reasoning: {decision.get('reasoning', 'N/A')}")
        pdf.ln(2)

        # Issues Section
        if report.get("all_unique_issues"):
            pdf.set_font("Arial", "B", 12)
            pdf.set_text_color(44, 62, 80)
            pdf.cell(0, 8, "ISSUES IDENTIFIED", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(2)

            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(0, 0, 0)
            for i, issue in enumerate(report.get("all_unique_issues", [])[:8], 1):
                pdf.set_x(20)
                pdf.cell(170, 5, f"{i}. {issue[:70]}", ln=True)
            pdf.ln(2)

        # Recommendations Section
        recommendations = _get_recommendations(decision_status, trust_score)
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 8, "RECOMMENDATIONS", ln=True)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0, 0, 0)
        for i, rec in enumerate(recommendations, 1):
            pdf.set_x(20)
            pdf.cell(170, 6, f"{i}. {rec[:70]}", ln=True)
        pdf.ln(3)

        # Footer
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 5, f"Generated: {report.get('timestamp', 'N/A')}", ln=True)
        pdf.cell(0, 5, "DocTome Medical Credential Verification System", ln=True)

        pdf.output(output_path)
        logger.info(f"[AGENT 3] PDF report generated: {output_path}")
        return True

    except Exception as e:
        logger.error(f"[AGENT 3] Failed to generate PDF: {str(e)}")
        return False

# ─────────────────────────────────────────────
# EMAIL SENDING
# ─────────────────────────────────────────────

def send_report_email(report: Dict[str, Any], report_file_path: str, recipient_email: str = "sarahriehe@gmail.com", from_email: str = None) -> bool:
    """
    Send final report via email using SendGrid API (with PDF attachment).

    Args:
        report: Final report dictionary
        report_file_path: Path to the JSON report file
        recipient_email: Email address to send to
        from_email: Sender email (must be verified in SendGrid). Defaults to recipient if not set.

    Returns:
        True if email sent successfully, False otherwise
    """
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        logger.warning("[AGENT 3] SendGrid not available or API key missing")
        return False

    try:
        # Use recipient email as sender if from_email not provided (self-reporting)
        if from_email is None:
            from_email = recipient_email

        # Prepare email content
        practitioner_name = report.get("practitioner", {}).get("full_name", "Unknown")
        decision = report.get("overall_decision", {}).get("status", "UNKNOWN")
        trust_score = report.get("overall_scoring", {}).get("average_trust_score", 0)

        subject = f"Medical Credential Verification Report - {practitioner_name} ({decision})"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c3e50;">Medical Credential Verification Report</h2>
                <p><strong>Practitioner:</strong> {practitioner_name}</p>
                <p><strong>Trust Score:</strong> {trust_score}/100</p>
                <p><strong>Decision:</strong> <span style="color: {'red' if decision == 'REJECTED' else 'orange' if decision == 'PENDING_REVIEW' else 'green'}; font-weight: bold;">{decision}</span></p>
                <p><strong>Reasoning:</strong> {report.get('overall_decision', {}).get('reasoning', 'N/A')}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">Detailed verification report attached as PDF.</p>
                <p style="color: #999; font-size: 11px;"><em>Generated: {report.get('timestamp', 'N/A')}</em></p>
            </body>
        </html>
        """

        # Generate PDF report
        pdf_path = report_file_path.replace('.json', '.pdf')
        pdf_generated = generate_pdf_report(report, pdf_path)

        if not pdf_generated:
            logger.warning("[AGENT 3] PDF generation failed, continuing with JSON attachment")
            pdf_path = report_file_path

        # Read attachment file for attachment
        with open(pdf_path, 'rb') as f:
            file_content = f.read()

        # Encode attachment as base64
        attachment_content = base64.b64encode(file_content).decode()

        # Determine attachment type and filename
        attachment_type = "application/pdf" if pdf_generated else "application/json"
        attachment_filename = os.path.basename(pdf_path) if pdf_generated else os.path.basename(report_file_path)

        # Build SendGrid API payload
        payload = {
            "personalizations": [
                {
                    "to": [{"email": recipient_email}],
                    "subject": subject
                }
            ],
            "from": {"email": from_email},
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ],
            "attachments": [
                {
                    "content": attachment_content,
                    "type": attachment_type,
                    "filename": attachment_filename,
                    "disposition": "attachment"
                }
            ]
        }

        # Send via SendGrid REST API
        headers = {
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(SENDGRID_API_URL, json=payload, headers=headers, timeout=15)

        if response.status_code in [200, 201, 202]:
            logger.info(f"[AGENT 3] Email sent successfully to {recipient_email} (Status: {response.status_code})")
            return True
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"[AGENT 3] Failed to send email: {error_msg}")

            if response.status_code == 403:
                logger.error(f"[AGENT 3] 403 Forbidden - Sender email '{from_email}' may not be verified in SendGrid")
                logger.error("[AGENT 3] Action: Verify the sender email in SendGrid dashboard (Settings > Sender Authentication)")
            elif response.status_code == 401:
                logger.error("[AGENT 3] 401 Unauthorized - API key is invalid or missing")

            return False

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[AGENT 3] Failed to send email: {error_msg}")
        return False


# ─────────────────────────────────────────────
# GROQ LLM DECISION MAKER
# ─────────────────────────────────────────────

def call_groq_decision(trust_score: float, all_issues: List[str], documents_verified: int) -> Dict[str, Any]:
    """Use Groq Llama to make intelligent decision with reasoning."""
    if not GROQ_AVAILABLE:
        logger.warning("Groq not available, using threshold-based decision")
        return make_threshold_decision(trust_score)

    if not GROQ_API_KEY:
        logger.warning("No Groq API key found, using threshold-based decision")
        return make_threshold_decision(trust_score)

    client = Groq(api_key=GROQ_API_KEY)

    issues_text = "\n".join(f"- {issue}" for issue in all_issues[:20])  # Top 20 issues

    prompt = f"""You are a medical credentials compliance officer. Analyze this practitioner's verification result:

Trust Score: {trust_score}/100
Documents Verified: {documents_verified}
Critical Issues Found ({len(all_issues)} total):
{issues_text}

Thresholds:
- Score > 85: AUTO_APPROVED
- Score < 50: AUTO_REJECTED
- Score 50-85: PENDING_HUMAN_REVIEW

Based on the score and issues, make a decision. Return ONLY valid JSON:
{{
  "decision": "<APPROVED|REJECTED|PENDING_REVIEW>",
  "decision_type": "<AUTO_APPROVED|AUTO_REJECTED|PENDING_HUMAN_REVIEW>",
  "reasoning": "<clear explanation why this decision was made>",
  "requires_human_review": <true|false>,
  "priority": "<LOW|MEDIUM|HIGH>",
  "recommendations": ["<action1>", "<action2>"]
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

        # Extract JSON object from response (handles extra text after JSON)
        response_text = response_text.strip()
        if '{' in response_text:
            json_start = response_text.index('{')
            json_end = response_text.rfind('}') + 1
            response_text = response_text[json_start:json_end]

        result = json.loads(response_text)
        logger.info(f"[GROQ DECISION] Decision: {result.get('decision')}, Priority: {result.get('priority')}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Groq decision response: {str(e)}")
        return make_threshold_decision(trust_score)
    except Exception as e:
        logger.error(f"Groq decision error: {str(e)}")
        return make_threshold_decision(trust_score)


def make_threshold_decision(trust_score: float) -> Dict[str, Any]:
    """
    Fallback: Make decision based on trust score thresholds.
    Returns (decision, reasoning).
    """
    if trust_score > APPROVED_THRESHOLD:
        return {
            "decision": "APPROVED",
            "decision_type": "AUTO_APPROVED",
            "reasoning": f"Trust score {trust_score}/100 exceeds approval threshold ({APPROVED_THRESHOLD}). Credentials verified automatically.",
            "requires_human_review": False,
            "priority": "LOW",
            "recommendations": ["Generate approval certificate", "Add to registry"]
        }
    elif trust_score < REJECTED_THRESHOLD:
        return {
            "decision": "REJECTED",
            "decision_type": "AUTO_REJECTED",
            "reasoning": f"Trust score {trust_score}/100 is below rejection threshold ({REJECTED_THRESHOLD}). Credentials appear suspicious or incomplete.",
            "requires_human_review": False,
            "priority": "HIGH",
            "recommendations": ["Request additional documentation", "Flag for audit"]
        }
    else:
        return {
            "decision": "PENDING_REVIEW",
            "decision_type": "PENDING_HUMAN_REVIEW",
            "reasoning": f"Trust score {trust_score}/100 falls in gray zone ({REJECTED_THRESHOLD}-{APPROVED_THRESHOLD}). Requires human verification.",
            "requires_human_review": True,
            "priority": "MEDIUM",
            "recommendations": ["Assign to compliance officer", "Schedule review meeting"]
        }

def generate_report(state: PractitionerState) -> Dict[str, Any]:
    """Generate comprehensive report with decision."""

    trust_score = state.get("trust_score", 0)
    all_issues = state.get("credential_flags", [])
    total_docs = state.get("verification_json_output", {}).get("total_documents_verified", 0)

    # Get intelligent decision from Groq LLM
    decision_result = call_groq_decision(trust_score, all_issues, total_docs)

    # Build report
    report = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "practitioner": {
            "practitioner_id": state.get("practitioner_id", "UNKNOWN"),
            "full_name": state.get("full_name", "N/A"),
            "specialty": state.get("specialty", "N/A"),
            "country": state.get("country", "N/A"),
            "registration_number": state.get("registration_number", "N/A")
        },
        "scoring": {
            "trust_score": trust_score,
            "total_documents_verified": total_docs,
            "average_extraction_quality": state.get("extraction_json_output", {}).get("summary", {}).get("average_quality", 0)
        },
        "decision": {
            "status": decision_result.get("decision"),
            "type": decision_result.get("decision_type"),
            "requires_human_review": decision_result.get("requires_human_review", False),
            "reasoning": decision_result.get("reasoning"),
            "priority": decision_result.get("priority", "MEDIUM"),
            "llm_analysis": "Decision enhanced with Groq LLM analysis"
        },
        "issues_found": all_issues,
        "documents_summary": {
            "total_documents": total_docs,
            "documents": state.get("verification_json_output", {}).get("documents_verified", [])
        },
        "extraction_summary": state.get("extraction_json_output", {}).get("summary", {}),
        "next_steps": decision_result.get("recommendations", _get_next_steps(decision_result.get("decision")))
    }

    return report

def _get_next_steps(decision: str) -> List[str]:
    """Get next steps based on decision."""
    if decision == "APPROVED":
        return [
            "Credentials verified automatically",
            "Generate approval certificate",
            "Add to trusted practitioners registry",
            "Notify practitioner of approval"
        ]
    elif decision == "REJECTED":
        return [
            "Flag credentials as suspicious",
            "Request additional documentation",
            "Notify practitioner of rejection",
            "Archive for audit trail"
        ]
    else:  # PENDING_REVIEW
        return [
            "Queue for human verification",
            "Assign to compliance officer",
            "Request supplementary documents if needed",
            "Schedule verification meeting"
        ]

# ─────────────────────────────────────────────
# MAIN AGENT
# ─────────────────────────────────────────────

async def report_agent(state: PractitionerState) -> PractitionerState:
    """Generate final reports for each document."""
    logger.info("[AGENT 3] Starting Report Generation for ALL documents...")

    try:
        # Get documents from verification results
        documents_verified = state.get("verification_json_output", {}).get("documents_verified", [])
        trust_score = state.get("trust_score", 0)
        all_issues = state.get("credential_flags", [])

        all_doc_reports = []

        # Generate individual report for each document
        for doc_index, doc_result in enumerate(documents_verified):
            logger.info(f"[AGENT 3] Generating report for document {doc_index + 1}/{len(documents_verified)}")

            doc_path = doc_result.get("document", f"document_{doc_index}")
            doc_name = os.path.splitext(os.path.basename(doc_path))[0]
            entity_type = doc_result.get("entity_type", "UNKNOWN")
            doc_trust_score = doc_result.get("scoring_details", {}).get("final_average_score", 0)
            doc_issues = doc_result.get("issues_found", [])

            # Get decision for this document using Groq
            decision_result = call_groq_decision(doc_trust_score, doc_issues, 1)

            # Build individual document report
            doc_report = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "document": {
                    "path": doc_path,
                    "name": doc_name,
                    "entity_type": entity_type
                },
                "practitioner": {
                    "practitioner_id": state.get("practitioner_id", "UNKNOWN"),
                    "full_name": state.get("full_name", "N/A"),
                    "specialty": state.get("specialty", "N/A"),
                    "country": state.get("country", "N/A"),
                    "registration_number": state.get("registration_number", "N/A")
                },
                "scoring": {
                    "document_trust_score": doc_trust_score,
                    "structural_score": doc_result.get("scoring_details", {}).get("structural_score", 0),
                    "semantic_score": doc_result.get("scoring_details", {}).get("semantic_score", 0)
                },
                "decision": {
                    "status": decision_result.get("decision"),
                    "type": decision_result.get("decision_type"),
                    "requires_human_review": decision_result.get("requires_human_review", False),
                    "reasoning": decision_result.get("reasoning"),
                    "priority": decision_result.get("priority", "MEDIUM"),
                    "llm_analysis": "Decision enhanced with Groq LLM analysis"
                },
                "issues_found": doc_issues,
                "analysis_summary": doc_result.get("analysis_summary", ""),
                "next_steps": decision_result.get("recommendations", _get_next_steps(decision_result.get("decision")))
            }

            # Save individual document report
            report_file = os.path.join(OUTPUT_FOLDER, f"{doc_name}_final_report.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(doc_report, f, indent=2, ensure_ascii=False)

            logger.info(f"[AGENT 3] Document report saved: {report_file}")
            all_doc_reports.append(doc_report)

        # Generate summary report across all documents
        overall_decision = call_groq_decision(trust_score, all_issues, len(documents_verified))

        summary_report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "practitioner": {
                "practitioner_id": state.get("practitioner_id", "UNKNOWN"),
                "full_name": state.get("full_name", "N/A"),
                "specialty": state.get("specialty", "N/A"),
                "country": state.get("country", "N/A"),
                "registration_number": state.get("registration_number", "N/A")
            },
            "overall_scoring": {
                "average_trust_score": trust_score,
                "total_documents": len(documents_verified),
                "average_extraction_quality": state.get("extraction_json_output", {}).get("summary", {}).get("average_quality", 0)
            },
            "overall_decision": {
                "status": overall_decision.get("decision"),
                "type": overall_decision.get("decision_type"),
                "requires_human_review": overall_decision.get("requires_human_review", False),
                "reasoning": overall_decision.get("reasoning"),
                "priority": overall_decision.get("priority", "MEDIUM"),
                "llm_analysis": "Decision enhanced with Groq LLM analysis"
            },
            "total_issues_found": len(set(all_issues)),
            "all_unique_issues": list(set(all_issues)),
            "document_reports": all_doc_reports,
            "next_steps": overall_decision.get("recommendations", _get_next_steps(overall_decision.get("decision")))
        }

        # Save summary report
        summary_file = os.path.join(OUTPUT_FOLDER, "final_report_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, indent=2, ensure_ascii=False)

        logger.info(f"[AGENT 3] Summary report saved: {summary_file}")
        logger.info(f"[AGENT 3] Generated {len(documents_verified)} individual document reports")

        # Send summary report via email (in background thread to avoid blocking)
        import asyncio
        logger.info("[AGENT 3] Sending summary report via email...")
        loop = asyncio.get_event_loop()
        try:
            email_sent = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: send_report_email(summary_report, summary_file, recipient_email="sarahriehe@gmail.com")),
                timeout=20
            )
            if email_sent:
                logger.info("[AGENT 3] Summary report email sent successfully")
            else:
                logger.warning("[AGENT 3] Failed to send summary report email (see warnings above)")
        except asyncio.TimeoutError:
            logger.warning("[AGENT 3] Email sending timed out, continuing without email")

        # Update state with decision
        state["final_decision"] = summary_report["overall_decision"]["status"]
        state["final_report"] = summary_report
        state["report_json_output"] = summary_report

        return state

    except Exception as e:
        logger.error(f"[AGENT 3] Error: {str(e)}")
        if "error_messages" not in state:
            state["error_messages"] = []
        state["error_messages"].append(f"Agent 3 Error: {str(e)}")
        return state

if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    async def test():
        print("\n" + "="*50)
        print("TESTING AGENT 3: REPORT GENERATION")
        print("="*50)

        # Test states
        test_cases = [
            {"trust_score": 90, "name": "High Score (APPROVED)"},
            {"trust_score": 72, "name": "Medium Score (PENDING_REVIEW)"},
            {"trust_score": 35, "name": "Low Score (REJECTED)"}
        ]

        for test_case in test_cases:
            state = {
                "practitioner_id": "test_001",
                "full_name": "Dr. Test",
                "specialty": "Cardiology",
                "country": "Algeria",
                "trust_score": test_case["trust_score"],
                "credential_flags": ["test_flag"],
                "verification_json_output": {"total_documents_verified": 3, "documents_verified": []},
                "extraction_json_output": {"summary": {"average_quality": 0.65}}
            }

            result = await report_agent(state)
            decision = result.get("final_decision")
            print(f"\n{test_case['name']}: {decision}")

    asyncio.run(test())
