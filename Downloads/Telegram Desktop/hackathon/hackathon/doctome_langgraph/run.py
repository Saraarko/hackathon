#!/usr/bin/env python
"""
Doctome LangGraph - Main Entry Point
Run from any directory: python run.py [command]
"""

import sys
import os
import asyncio

# Set working directory to script directory so relative paths work
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Add to path so agents module can be imported
sys.path.insert(0, SCRIPT_DIR)

from agents import extraction_agent, verification_agent, risk_assessment_agent, PractitionerState
from agents.agent1_extraction import main_test as test_extraction
from datetime import datetime

def show_help():
    print("\n" + "="*70)
    print("DOCTOME - Medical Verification System")
    print("="*70)
    print("\nUsage: python run.py [command]")
    print("\nAvailable Commands:")
    print("  agent1        - Test Agent 1 (Document Extraction)")
    print("  agent2        - Test Agent 2 (Credential Verification)")
    print("  agent3        - Test Agent 3 (Risk Assessment)")
    print("  workflow      - Run full 3-agent workflow")
    print("  help          - Show this help message")
    print("\nExamples:")
    print("  python run.py agent1")
    print("  python run.py workflow")
    print()

async def run_agent1():
    """Run Agent 1 test"""
    print("\n[Running] Agent 1: Document Extraction\n")
    result = await test_extraction()
    print("\n[Success] Agent 1 completed")
    return result

async def run_full_workflow():
    """Run full workflow (not yet implemented)"""
    print("\n[Running] Full Workflow (Agents 1→2→3)\n")
    print("[TODO] Full workflow will be implemented with Agents 2 & 3")
    await run_agent1()

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    try:
        if command == "agent1":
            asyncio.run(run_agent1())
        elif command == "agent2":
            print("[TODO] Agent 2 not yet tested")
        elif command == "agent3":
            print("[TODO] Agent 3 not yet tested")
        elif command == "workflow":
            asyncio.run(run_full_workflow())
        elif command == "help":
            show_help()
        else:
            print(f"Unknown command: {command}")
            show_help()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
