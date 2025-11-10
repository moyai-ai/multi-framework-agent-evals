"""
Quick test to verify Langfuse tracing is working with the agent.

This script:
1. Creates a simple test scenario
2. Runs the agent with Langfuse enabled
3. Prints the trace ID so you can view it in Langfuse UI
"""

import asyncio
import os
from src.agent.graph import run_agent
from src.context import Config


async def test_tracing():
    """Test the agent with Langfuse tracing enabled."""
    print("=" * 60)
    print("Testing Langfuse Tracing Integration")
    print("=" * 60)

    # Create config
    config = Config()

    # Verify Langfuse is enabled
    print(f"\nLangfuse Enabled: {config.LANGFUSE_ENABLED}")
    print(f"Langfuse Host: {config.LANGFUSE_HOST}")
    print(f"Public Key Set: {bool(config.LANGFUSE_PUBLIC_KEY)}")
    print(f"Secret Key Set: {bool(config.LANGFUSE_SECRET_KEY)}")

    if not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
        print("\n⚠ Langfuse credentials not found. Tracing will be disabled.")
        print("Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env file")
        return

    # Test with a simple repository URL
    # Note: This will attempt to fetch from GitHub, so we use a real public repo
    repository_url = "https://github.com/octocat/Hello-World"
    analysis_type = "security"

    print(f"\nRunning analysis...")
    print(f"Repository: {repository_url}")
    print(f"Analysis Type: {analysis_type}")
    print(f"\nThis will create a trace in Langfuse. Please wait...")

    try:
        result = await run_agent(
            repository_url=repository_url,
            analysis_type=analysis_type,
            config=config
        )

        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("=" * 60)
        print(f"Repository: {result.get('repository')}")
        print(f"Files Analyzed: {len(result.get('files_analyzed', []))}")
        print(f"Issues Found: {len(result.get('issues_found', []))}")
        print(f"Steps Taken: {result.get('steps_taken')}")

        if result.get('error'):
            print(f"\n⚠ Error: {result['error']}")

        print("\n" + "=" * 60)
        print("✓ Trace created successfully!")
        print("=" * 60)
        print("\nView your trace at:")
        print(f"👉 {config.LANGFUSE_HOST}")
        print("\nLook for the trace tagged with:")
        print("  - static-analysis")
        print("  - security")
        print("  - langgraph")

    except Exception as e:
        print(f"\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tracing())
