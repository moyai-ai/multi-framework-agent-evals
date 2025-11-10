"""
Test script to verify Langfuse integration with the static code analysis agent.

This script demonstrates:
1. Agent creation with Langfuse enabled/disabled
2. Configuration validation
3. Basic import and initialization checks

Usage:
    # Without Langfuse (should work without credentials)
    python test_langfuse_integration.py

    # With Langfuse (requires credentials in .env)
    LANGFUSE_ENABLED=true python test_langfuse_integration.py
"""

import os
import sys


def test_imports():
    """Test that all necessary modules can be imported."""
    print("Testing imports...")
    try:
        from src.agent.graph import create_agent, run_agent
        from src.context import Config
        from langfuse import get_client
        from langfuse.langchain import CallbackHandler
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_agent_creation_without_langfuse():
    """Test agent creation with Langfuse disabled."""
    print("\nTesting agent creation without Langfuse...")
    try:
        from src.agent.graph import create_agent
        from src.context import Config

        config = Config()
        config.LANGFUSE_ENABLED = False
        config.OPENAI_API_KEY = "test-key"  # Dummy key for testing

        agent = create_agent(config)
        print("✓ Agent created successfully without Langfuse")
        return True
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        return False


def test_langfuse_configuration():
    """Test Langfuse configuration loading."""
    print("\nTesting Langfuse configuration...")
    try:
        from src.context import Config

        config = Config()

        print(f"  LANGFUSE_ENABLED: {config.LANGFUSE_ENABLED}")
        print(f"  LANGFUSE_HOST: {config.LANGFUSE_HOST}")
        print(
            f"  LANGFUSE_PUBLIC_KEY: {'SET' if config.LANGFUSE_PUBLIC_KEY else 'NOT SET'}"
        )
        print(
            f"  LANGFUSE_SECRET_KEY: {'SET' if config.LANGFUSE_SECRET_KEY else 'NOT SET'}"
        )

        if config.LANGFUSE_ENABLED:
            if config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY:
                print("✓ Langfuse configuration complete")
                return True
            else:
                print(
                    "⚠ Langfuse enabled but credentials not set (tracing will be disabled)"
                )
                return True
        else:
            print("✓ Langfuse disabled (tracing will not occur)")
            return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_langfuse_authentication():
    """Test Langfuse authentication if credentials are available."""
    print("\nTesting Langfuse authentication...")
    try:
        from src.context import Config
        from langfuse import get_client

        config = Config()

        if not config.LANGFUSE_ENABLED:
            print("⊘ Langfuse disabled, skipping authentication test")
            return True

        if not config.LANGFUSE_PUBLIC_KEY or not config.LANGFUSE_SECRET_KEY:
            print("⊘ Langfuse credentials not set, skipping authentication test")
            return True

        # Set environment variables for Langfuse client
        os.environ["LANGFUSE_PUBLIC_KEY"] = config.LANGFUSE_PUBLIC_KEY
        os.environ["LANGFUSE_SECRET_KEY"] = config.LANGFUSE_SECRET_KEY
        os.environ["LANGFUSE_HOST"] = config.LANGFUSE_HOST

        client = get_client()
        if client.auth_check():
            print("✓ Langfuse authentication successful")
            return True
        else:
            print("✗ Langfuse authentication failed")
            return False
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Langfuse Integration Test Suite")
    print("=" * 60)

    tests = [
        test_imports,
        test_agent_creation_without_langfuse,
        test_langfuse_configuration,
        test_langfuse_authentication,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
