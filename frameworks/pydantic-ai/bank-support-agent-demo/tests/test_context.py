#!/usr/bin/env python
"""Test context persistence between agent runs."""

import asyncio
import os
from src.agents import get_initial_agent
from src.context import create_initial_context

# Set API key from environment
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")

async def test_context_persistence():
    """Test if context persists between agent runs."""
    try:
        print("Creating initial context...")
        context = create_initial_context()
        print(f"Initial: authenticated={context.authenticated}")

        print("\nFirst run - authenticating...")
        agent1 = get_initial_agent()
        result1 = await agent1.run(
            "My email is test@example.com and the last 4 of my SSN is 1234",
            deps=context
        )
        print(f"Response: {result1.output[:100]}...")
        print(f"After auth: authenticated={context.authenticated}")
        print(f"Customer: {context.customer.name if context.customer else 'None'}")

        # Use the same context for the second run
        print("\nSecond run - checking balance with same context...")
        agent2 = get_initial_agent()  # Fresh agent
        result2 = await agent2.run(
            "Show me my account balances",
            deps=context  # Same context
        )
        print(f"Response: {result2.output[:200]}...")
        print(f"Still authenticated: {context.authenticated}")

        print("\n✓ Test completed!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_context_persistence())