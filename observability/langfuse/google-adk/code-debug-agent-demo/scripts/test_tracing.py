#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "google-adk>=1.0.0",
#   "google-cloud-aiplatform[adk,agent-engines]>=1.93.0",
#   "google-genai>=1.9.0",
#   "langfuse>=2.0.0",
#   "python-dotenv>=1.0.0",
#   "beautifulsoup4>=4.12.0",
#   "httpx>=0.28.0",
#   "stackapi>=0.3.0",
#   "tenacity>=9.0.0",
# ]
# ///
"""Quick test script to verify Langfuse tracing improvements.

This script runs a simple scenario and checks that traces are properly named.

Usage:
    uv run scripts/test_tracing.py

Requirements:
    - GOOGLE_API_KEY environment variable set
    - LANGFUSE_PUBLIC_KEY environment variable set
    - LANGFUSE_SECRET_KEY environment variable set
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.traced_runner import TracedAgentRunner, run_traced_scenario
from langfuse import get_client


async def test_tracing():
    """Test the improved tracing setup."""
    print("=" * 60)
    print("TESTING LANGFUSE TRACING IMPROVEMENTS")
    print("=" * 60)

    # Test 1: Simple agent execution
    print("\nTest 1: Simple Agent Execution")
    print("-" * 40)

    runner = TracedAgentRunner(agent_name="quick_debug_agent")

    test_prompt = "ImportError: No module named 'pandas'"
    print(f"Prompt: {test_prompt}")

    try:
        response_parts = []
        async for event in runner.run_traced(
            prompt=test_prompt,
            user_id="test_user_tracing",
            session_id="test_session_tracing",
            metadata={"test_type": "tracing_verification"}
        ):
            # Just collect events, don't print everything
            if hasattr(event, 'content'):
                response_parts.append(str(event))

        print(f"✓ Agent execution completed")
        print(f"  Events received: {len(response_parts)}")

    except Exception as e:
        print(f"✗ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Scenario execution
    print("\nTest 2: Scenario Execution")
    print("-" * 40)

    scenario_data = {
        "name": "Tracing Test Scenario",
        "error_message": "TypeError: Cannot read property 'map' of undefined",
        "programming_language": "javascript",
        "framework": "react"
    }

    print(f"Scenario: {scenario_data['name']}")

    try:
        result = await run_traced_scenario(
            scenario_data=scenario_data,
            agent_name="quick_debug_agent",
            user_id="test_user_scenario"
        )

        if result.get("success"):
            print(f"✓ Scenario execution completed successfully")
            print(f"  Response length: {len(result.get('response', ''))}")
        else:
            print(f"✗ Scenario execution failed: {result.get('error')}")

    except Exception as e:
        print(f"✗ Scenario execution failed: {e}")
        import traceback
        traceback.print_exc()

    # Flush Langfuse to ensure all traces are sent
    print("\nFlushing traces to Langfuse...")
    langfuse = get_client()
    langfuse.flush()
    print("✓ Traces flushed")

    print("\n" + "=" * 60)
    print("TRACING TEST COMPLETE")
    print("=" * 60)
    print("\nTo validate traces:")
    print("1. Check Langfuse UI for traces named:")
    print("   - 'Code Debug: quick_debug_agent'")
    print("   - 'Scenario Test: Tracing Test Scenario'")
    print("\n2. Or run: python scripts/export_traces.py --validate")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tracing())
