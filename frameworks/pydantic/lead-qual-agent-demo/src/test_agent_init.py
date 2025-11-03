#!/usr/bin/env python
"""Test agent initialization with mock API keys."""

import sys
import os

# Add the parent directory to the path to fix imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set mock API keys for testing
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["LINKUP_API_KEY"] = "test-linkup-key"

print("Testing Agent initialization...")

try:
    from src.agent.lead_qualifier import LeadQualificationAgent
    print("✓ Successfully imported LeadQualificationAgent")
except ImportError as e:
    print(f"✗ Failed to import LeadQualificationAgent: {e}")
    sys.exit(1)

try:
    # Try to initialize the agent
    agent = LeadQualificationAgent(model="gpt-4o-mini")
    print("✓ Successfully initialized LeadQualificationAgent")
    print(f"  Agent: {agent}")
    print(f"  Agent.agent: {agent.agent}")
    print(f"  Search tool: {agent.search_tool}")
except Exception as e:
    print(f"✗ Error initializing LeadQualificationAgent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Agent initialization successful!")
print("\nNote: This test uses mock API keys. For real usage:")
print("1. Set valid OPENAI_API_KEY in .env")
print("2. Set valid LINKUP_API_KEY in .env")