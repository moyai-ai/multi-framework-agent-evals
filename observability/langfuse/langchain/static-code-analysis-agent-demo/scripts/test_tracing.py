#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "langchain>=0.3.0",
#   "langchain-openai>=0.2.0",
#   "langgraph>=0.2.0",
#   "langfuse>=2.0.0",
#   "python-dotenv>=1.0.0",
# ]
# ///
"""Quick test script to verify Langfuse tracing improvements.

This script runs a simple scenario and checks that traces are properly named.

Usage:
    uv run scripts/test_tracing.py

Requirements:
    - OPENAI_API_KEY environment variable set
    - LANGFUSE_PUBLIC_KEY environment variable set
    - LANGFUSE_SECRET_KEY environment variable set
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.graph import run_agent
from langfuse import get_client


async def test_tracing():
    """Test the improved tracing setup."""
    print("=" * 60)
    print("TESTING LANGFUSE TRACING IMPROVEMENTS")
    print("=" * 60)

    # Test 1: Simple agent execution
    print("\nTest 1: Simple Agent Execution")
    print("-" * 40)

    test_repo = "https://github.com/example/test-repo"
    print(f"Repository: {test_repo}")
    print(f"Analysis type: security")

    try:
        result = await run_agent(
            repository_url=test_repo,
            analysis_type="security",
            user_id="test_user_tracing",
            session_id="test_session_tracing",
            scenario_name="tracing_verification"
        )

        if not result.get("error"):
            print(f"✓ Agent execution completed")
            print(f"  Files analyzed: {len(result.get('files_analyzed', []))}")
            print(f"  Issues found: {len(result.get('issues_found', []))}")
            print(f"  Steps taken: {result.get('steps_taken', 0)}")
        else:
            print(f"✗ Agent execution failed: {result.get('error')}")

    except Exception as e:
        print(f"✗ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Different analysis type
    print("\nTest 2: Quality Analysis")
    print("-" * 40)

    print(f"Repository: {test_repo}")
    print(f"Analysis type: quality")

    try:
        result = await run_agent(
            repository_url=test_repo,
            analysis_type="quality",
            user_id="test_user_quality",
            session_id="test_session_quality",
            scenario_name="quality_check"
        )

        if not result.get("error"):
            print(f"✓ Agent execution completed")
            print(f"  Files analyzed: {len(result.get('files_analyzed', []))}")
            print(f"  Issues found: {len(result.get('issues_found', []))}")
        else:
            print(f"✗ Agent execution failed: {result.get('error')}")

    except Exception as e:
        print(f"✗ Agent execution failed: {e}")
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
    print("   - 'static-code-analysis-agent: security analysis [tracing_verification] - example/test-repo'")
    print("   - 'static-code-analysis-agent: quality analysis [quality_check] - example/test-repo'")
    print("\n2. Or run: uv run scripts/export_traces.py --validate")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tracing())
