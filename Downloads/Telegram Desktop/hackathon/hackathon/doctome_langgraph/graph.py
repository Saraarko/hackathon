"""
LangGraph Workflow - Main Graph Definition
Orchestrates the 3-agent verification pipeline for medical practitioners
"""

import logging
from langgraph.graph import StateGraph, END
from agents import PractitionerState, extraction_agent, verification_agent, report_agent
from datetime import datetime

logger = logging.getLogger("doctome.graph")


def create_medical_verification_graph():
    """
    Create LangGraph workflow for medical practitioner verification.

    Graph structure:
    START → Agent1 (Extraction) → Agent2 (Verification) → END

    Each agent:
    1. Reads from shared state
    2. Processes its domain
    3. Updates state with results
    4. Next agent uses updated state

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("[GRAPH] Creating medical verification graph...")

    # Create state graph
    graph = StateGraph(PractitionerState)

    # Add nodes (agents)
    graph.add_node("extraction", extraction_agent)
    graph.add_node("verification", verification_agent)
    graph.add_node("report", report_agent)

    # Add edges (sequential workflow)
    # Each agent's output becomes next agent's input via shared state
    graph.add_edge("extraction", "verification")      # Extract → Verify
    graph.add_edge("verification", "report")          # Verify → Report
    graph.add_edge("report", END)                     # Report → End

    # Set entry point
    graph.set_entry_point("extraction")

    # Compile
    app = graph.compile()

    logger.info("[GRAPH] Graph compiled successfully")
    logger.info("[GRAPH] Workflow: Extraction → Verification → Report")

    return app


async def run_verification_workflow(
    practitioner_id: str,
    full_name: str,
    specialty: str,
    country: str,
    registration_number: str,
    documents: list,
    submission_time: str = None
) -> PractitionerState:
    """
    Run the complete medical verification workflow.

    This is the main entry point for the system.

    Args:
        practitioner_id: Unique ID for practitioner
        full_name: Full legal name
        specialty: Medical specialty
        country: Country of practice
        registration_number: Medical license number
        documents: List of dicts with "path" and "type"
        submission_time: ISO format timestamp (optional)

    Returns:
        Final state with all agent results and decision

    Example:
        result = await run_verification_workflow(
            practitioner_id="pract_123",
            full_name="Dr. Ahmed Ben Ali",
            specialty="Cardiology",
            country="Algeria",
            registration_number="12345ABC",
            documents=[
                {"path": "diploma.pdf", "type": "diploma"},
                {"path": "license.pdf", "type": "license"}
            ]
        )

        print(f"Decision: {result['decision']}")
        print(f"Trust Score: {result['final_trust_score']}/100")
        print(f"Reasoning: {result['final_reasoning']}")
    """
    logger.info(f"[WORKFLOW] Starting verification for {practitioner_id}")

    try:
        # Create initial state
        initial_state = PractitionerState(
            practitioner_id=practitioner_id,
            full_name=full_name,
            specialty=specialty,
            country=country,
            registration_number=registration_number,
            documents=documents,
            submission_time=submission_time or datetime.now().isoformat(),
            error_messages=[],
            processing_log=[
                f"[{datetime.now().isoformat()}] Workflow started"
            ]
        )

        logger.info(f"[WORKFLOW] Initial state created")

        # Get or create graph
        verification_graph = create_medical_verification_graph()

        # Run workflow (ainvoke for async agents)
        logger.info("[WORKFLOW] Invoking graph...")
        final_state = await verification_graph.ainvoke(initial_state)

        logger.info(f"[WORKFLOW] Workflow complete for {practitioner_id}")
        logger.info(f"[WORKFLOW] Final decision: {final_state.get('decision')}")
        logger.info(f"[WORKFLOW] Final score: {final_state.get('final_trust_score')}/100")

        return final_state

    except Exception as e:
        logger.error(f"[WORKFLOW] Critical error: {str(e)}")
        raise


# Main graph instance (can be reused)
verification_graph = create_medical_verification_graph()


# ==================== FOR TESTING ====================

if __name__ == "__main__":
    """
    Test the workflow locally.

    Usage:
        python graph.py
    """
    import asyncio

    async def test_workflow():
        """Test workflow with sample data."""
        logging.basicConfig(level=logging.INFO)

        print("\n" + "="*60)
        print("DOCTOME - Medical Practitioner Verification Workflow")
        print("="*60 + "\n")

        result = await run_verification_workflow(
            practitioner_id="test_pract_001",
            full_name="Dr. Ahmed Ben Ali",
            specialty="Cardiology",
            country="Algeria",
            registration_number="12345ABC",
            documents=[
                {"path": "test_diploma.pdf", "type": "diploma"},
                {"path": "test_license.pdf", "type": "license"},
                {"path": "test_id.pdf", "type": "id"}
            ]
        )

        print("\n" + "="*60)
        print("VERIFICATION COMPLETE")
        print("="*60)
        print(f"\nExtracted Documents: {result.get('extraction_json_output', {}).get('summary', {}).get('total_documents', 0)}")
        print(f"Trust Score: {result.get('trust_score', 'N/A')}/100")
        print(f"Flags: {result.get('credential_flags', [])}")
        print(f"Errors: {result.get('error_messages', [])}")

        print("\n" + "="*60)
        print("PROCESSING LOG")
        print("="*60)
        for log in result.get("processing_log", []):
            print(log)

    # Run test
    asyncio.run(test_workflow())
