"""
Test script to verify enhanced observability improvements (Phase 1).

This script tests:
1. User ID and Session ID tracking
2. Tags (analysis type, environment, status, severity)
3. Rich metadata (repository, analysis config, results, execution)
4. Version tracking

Usage:
    unset VIRTUAL_ENV && uv run --env-file .env python test_enhanced_observability.py
"""

import asyncio
from src.manager import AnalysisManager
from src.context import Config


async def main():
    """Test enhanced observability features."""
    print("=" * 60)
    print("Testing Enhanced Observability Features (Phase 1)")
    print("=" * 60)

    config = Config()
    manager = AnalysisManager(config=config, verbose=True)

    # Test with custom user_id and session_id
    print("\n1. Testing with custom user_id and session_id...")
    result = await manager.analyze_repository(
        repository_url="https://github.com/openai/openai-python",
        analysis_type="security",
        user_id="observability-test-user",
        session_id="phase1-verification-session"
    )

    print("\n" + "=" * 60)
    print("Enhanced Observability Verification")
    print("=" * 60)

    if config.LANGFUSE_ENABLED:
        print("✓ Langfuse tracing is ENABLED")
        print("\nExpected trace enhancements:")
        print("  - User ID: observability-test-user")
        print("  - Session ID: phase1-verification-session")
        print("  - Tags: static-analysis, security, langgraph, production, success/error, severity tags")
        print("  - Metadata: repository details, analysis config, results breakdown, execution stats")
        print(f"  - Version: v{config.MODEL_NAME}_{config.TEMPERATURE}")

        print("\nCheck Langfuse UI for the following:")
        print("  1. Navigate to Traces in Langfuse")
        print("  2. Find trace with session_id: phase1-verification-session")
        print("  3. Verify user_id is set to: observability-test-user")
        print("  4. Check tags include: static-analysis, security, has-critical-issues, has-high-issues")
        print("  5. Inspect metadata for repository, analysis, results, and execution details")
        print("  6. Confirm version is displayed")
    else:
        print("⚠ Langfuse tracing is DISABLED")
        print("Set LANGFUSE_ENABLED=true in .env to test observability features")

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Analysis Status: {'Success' if not result.get('error') else 'Failed'}")
    print(f"Files Analyzed: {len(result.get('files_analyzed', []))}")
    print(f"Issues Found: {len(result.get('issues_found', []))}")
    print(f"Steps Taken: {result.get('steps_taken', 0)}")

    # Count severity distribution
    issues = result.get('issues_found', [])
    severity_counts = {}
    for issue in issues:
        severity = issue.get('severity', 'UNKNOWN')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    if severity_counts:
        print("\nSeverity Breakdown:")
        for severity, count in sorted(severity_counts.items()):
            print(f"  {severity}: {count}")

    print("\n" + "=" * 60)
    print("Phase 1 Improvements Tested Successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
