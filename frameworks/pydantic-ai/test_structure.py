#!/usr/bin/env python
"""Test that the structure is correct without requiring API key."""

import sys
import os

# Set a dummy API key for testing imports
os.environ["OPENAI_API_KEY"] = "test-key-for-import"

try:
    # Test imports
    from src.context import BankSupportContext, create_initial_context
    from src.tools import BANK_SUPPORT_TOOLS, get_all_tools
    from src.agents import AGENTS, get_initial_agent, list_agents
    from src.runner import ScenarioRunner, TestScenario

    print("✓ All imports successful")

    # Test context creation
    context = create_initial_context()
    print("✓ Context creation successful")

    # Test tools
    tools = get_all_tools()
    print(f"✓ Found {len(tools)} tools")

    # Test agents
    agents = list_agents()
    print(f"✓ Found {len(agents)} agents")

    # Verify agent names
    for agent_info in agents:
        print(f"  - {agent_info['name']}: {len(agent_info['tools'])} tools")

    print("\n✓ All structure tests passed!")
    sys.exit(0)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)