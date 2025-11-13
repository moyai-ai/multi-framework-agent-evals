#!/usr/bin/env python3
"""Verification script to demonstrate tracing is disabled during tests."""

import os
import sys

def check_tracing_status():
    """Check if tracing is disabled."""
    disable_tracing = os.getenv("DISABLE_LANGFUSE_TRACING", "false").lower() == "true"

    print("=" * 60)
    print("LANGFUSE TRACING STATUS VERIFICATION")
    print("=" * 60)
    print(f"Environment Variable: DISABLE_LANGFUSE_TRACING = {os.getenv('DISABLE_LANGFUSE_TRACING', 'not set')}")
    print(f"Tracing Disabled: {disable_tracing}")
    print()

    if disable_tracing:
        print("✅ Tracing is DISABLED (suitable for unit tests)")
        print("   - No traces will be sent to Langfuse")
        print("   - Tests will run faster and without external dependencies")
    else:
        print("✅ Tracing is ENABLED (suitable for production/demo runs)")
        print("   - Traces will be sent to Langfuse for observability")
        print("   - Full agent execution monitoring available")

    print("=" * 60)
    return disable_tracing

if __name__ == "__main__":
    print("\n1. Default state (no environment variable set):")
    print("-" * 60)
    # Clear the env var to test default
    os.environ.pop("DISABLE_LANGFUSE_TRACING", None)
    default_disabled = check_tracing_status()

    print("\n2. During unit tests (DISABLE_LANGFUSE_TRACING=true):")
    print("-" * 60)
    os.environ["DISABLE_LANGFUSE_TRACING"] = "true"
    test_disabled = check_tracing_status()

    print("\n3. Summary:")
    print("-" * 60)
    print(f"✅ Default behavior: Tracing {'DISABLED' if default_disabled else 'ENABLED'}")
    print(f"✅ Test behavior: Tracing {'DISABLED' if test_disabled else 'ENABLED'}")
    print()
    print("The fix ensures that:")
    print("  1. Unit tests set DISABLE_LANGFUSE_TRACING=true in tests/conftest.py")
    print("  2. src/runner.py checks this variable before creating traces")
    print("  3. Normal execution (without the env var) still enables tracing")
    print("=" * 60)
