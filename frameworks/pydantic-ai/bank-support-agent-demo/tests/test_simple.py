#!/usr/bin/env python
"""Simple test of agent run without scenarios."""

import asyncio
import os
from src.agents import get_initial_agent
from src.context import create_initial_context

# Set API key from environment or dummy
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")

async def test_simple_run():
    """Test a simple agent run."""
    try:
        print("Creating agent...")
        agent = get_initial_agent()
        print(f"Agent created: {agent.name}")

        print("\nCreating context...")
        context = create_initial_context()
        print(f"Context created: session_id={context.session_id}")

        print("\nRunning agent...")
        result = await agent.run(
            "Hello",
            deps=context
        )

        print(f"\nResult type: {type(result)}")
        print(f"Has output: {hasattr(result, 'output')}")
        if hasattr(result, 'output'):
            print(f"Output: {result.output}")

        print("\n✓ Test completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_run())