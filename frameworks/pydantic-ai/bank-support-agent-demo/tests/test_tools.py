#!/usr/bin/env python
"""Test if agent can call tools."""

import asyncio
import os
from src.agents import get_initial_agent
from src.context import create_initial_context

# Set API key from environment
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")

async def test_tool_calling():
    """Test if agent calls authenticate_customer tool."""
    try:
        print("Creating agent...")
        agent = get_initial_agent()
        print(f"Agent created: {agent.name}")

        print("\nCreating context...")
        context = create_initial_context()
        print(f"Context created: authenticated={context.authenticated}")

        print("\nRunning agent with authentication request...")
        result = await agent.run(
            "My email is test@example.com and the last 4 of my SSN is 1234",
            deps=context
        )

        print(f"\nResult type: {type(result)}")

        # Check if tools were called
        if hasattr(result, 'all_messages'):
            messages = result.all_messages()
            print(f"Total messages: {len(messages)}")
            for i, msg in enumerate(messages):
                print(f"Message {i}: {type(msg)} - {getattr(msg, 'role', 'unknown')}")
                if hasattr(msg, 'parts'):
                    for part in msg.parts:
                        print(f"  Part: {type(part)} - {part}")

        # Check the output
        if hasattr(result, 'output'):
            print(f"\nOutput: {result.output}")

        # Check context changes
        print(f"\nContext after: authenticated={context.authenticated}")
        print(f"Customer: {context.customer}")
        print(f"Customer ID: {context.customer_id}")

        print("\n✓ Test completed!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_calling())