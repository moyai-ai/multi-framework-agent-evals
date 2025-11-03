#!/usr/bin/env python
"""Test the Pydantic AI API to understand AgentRunResult structure."""

import asyncio
import os
from pydantic_ai import Agent

# Set a dummy API key for testing
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")

async def test_agent_result():
    """Test agent result structure."""
    try:
        # Create a simple agent
        agent = Agent(
            model="gpt-4o",
            system_prompt="You are a helpful assistant.",
        )

        # Run the agent
        result = await agent.run("Hello")

        # Check available attributes
        print("AgentRunResult attributes:")
        for attr in dir(result):
            if not attr.startswith('_'):
                print(f"  - {attr}: {type(getattr(result, attr))}")

        # Try to get the response text
        if hasattr(result, 'data'):
            print(f"\nResponse via .data: {result.data}")
        if hasattr(result, 'response'):
            print(f"\nResponse via .response: {result.response}")
        if hasattr(result, 'messages'):
            print(f"\nResponse via .messages: {result.messages}")
        if hasattr(result, 'all_messages'):
            print(f"\nResponse via .all_messages: {result.all_messages}")

    except Exception as e:
        print(f"Error during test: {e}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    asyncio.run(test_agent_result())