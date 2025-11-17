"""Pytest configuration and fixtures."""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Disable actual API calls during tests if needed
    os.environ["TESTING"] = "1"

    # Mock API keys if not set
    if not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = "test_google_api_key"

    if not os.getenv("JUDGMENT_API_KEY"):
        os.environ["JUDGMENT_API_KEY"] = "test_judgment_api_key"

    if not os.getenv("JUDGMENT_ORG_ID"):
        os.environ["JUDGMENT_ORG_ID"] = "test_org_id"


@pytest.fixture
def sample_scenario():
    """Provide a sample scenario for testing."""
    return {
        "name": "Test Scenario",
        "description": "A test scenario for unit testing",
        "error_message": "ImportError: No module named 'test_module'",
        "programming_language": "python",
        "expected_tools": ["search_stack_exchange_for_error"],
        "expected_keywords": ["pip install", "module"],
    }
