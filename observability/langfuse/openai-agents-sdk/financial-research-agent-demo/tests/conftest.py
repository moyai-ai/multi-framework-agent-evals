"""
Pytest configuration and shared fixtures for the test suite.
"""

import os
import pytest
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

from src.runner import ScenarioRunner
from src.context import FinancialResearchContext, create_initial_context
from src.agents import AGENTS


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging to prevent closed file errors during test cleanup."""
    # Store original handlers
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()

    # Create a persistent handler that won't be closed by pytest
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.WARNING)  # Only show warnings and errors
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Configure httpx logger to use stderr and not fail on closed stdout
    httpx_logger = logging.getLogger('httpx')
    httpx_logger.handlers.clear()
    httpx_logger.addHandler(handler)
    httpx_logger.propagate = False

    yield

    # Restore original handlers
    root_logger.handlers = original_handlers


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Automatically set up test environment for unit tests.
    
    For unit tests, sets a mock API key if one isn't already present.
    Integration tests should set OPENAI_API_KEY in their environment.
    
    IMPORTANT: Disables Langfuse tracing for all unit tests by unsetting
    the Langfuse environment variables.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "test-key-12345-mock-for-unit-tests"
    
    # Explicitly disable Langfuse tracing for all unit tests
    # Unset Langfuse keys to prevent tracing
    os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
    os.environ.pop("LANGFUSE_SECRET_KEY", None)
    os.environ.pop("LANGFUSE_HOST", None)
    # Set a flag to indicate tracing is disabled
    os.environ["LANGFUSE_DISABLED"] = "true"

    yield


@pytest.fixture
def mock_openai_api_key(monkeypatch):
    """Mock OpenAI API key for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")


@pytest.fixture
def disable_langfuse_tracing(monkeypatch):
    """Explicitly disable Langfuse tracing for a test."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.setenv("LANGFUSE_DISABLED", "true")


@pytest.fixture
def scenario_runner():
    """Create a scenario runner instance."""
    return ScenarioRunner(verbose=False)


@pytest.fixture
def sample_context():
    """Create a sample context for testing."""
    return FinancialResearchContext(
        query="Analyze Apple Inc",
        company_name="Apple Inc",
        analysis_type="company_analysis",
        search_plan=["Apple earnings", "Apple iPhone sales", "Apple AI strategy"],
        current_stage="planning"
    )


@pytest.fixture
def initial_context():
    """Create an initial context."""
    return create_initial_context(query="Test query")


@pytest.fixture
def all_agents():
    """Get all available agents."""
    return AGENTS


@pytest.fixture
def scenario_files():
    """Get all scenario JSON files."""
    import src
    src_path = Path(src.__file__).parent
    scenarios_dir = src_path / "scenarios"
    return list(scenarios_dir.glob("*.json"))


@pytest.fixture
def sample_scenario_dict():
    """Sample scenario dictionary for testing."""
    return {
        "name": "Test Scenario",
        "description": "A test scenario for unit testing",
        "query": "Analyze test company",
        "expectations": {
            "min_search_terms": 3,
            "required_sections": ["Executive Summary"],
            "verification_should_pass": True,
            "min_report_length": 100
        },
        "metadata": {
            "test_type": "unit_test"
        }
    }


@pytest.fixture
def temp_scenario_file(tmp_path, sample_scenario_dict):
    """Create a temporary scenario file for testing."""
    import json

    scenario_file = tmp_path / "test_scenario.json"
    with open(scenario_file, 'w') as f:
        json.dump(sample_scenario_dict, f)

    return scenario_file


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return {
        "Apple earnings 2024": "Apple reported strong Q4 earnings with revenue up 6%...",
        "Apple iPhone sales": "iPhone sales remain strong in emerging markets...",
        "Apple AI strategy": "Apple focusing on on-device AI processing..."
    }


@pytest.fixture
def sample_report():
    """Sample financial report for testing."""
    return """
# Apple Inc Financial Analysis

## Executive Summary

Apple Inc demonstrated strong financial performance in Q4 2024 with revenue growth of 6% YoY.

## Financial Performance

Revenue reached $89.5B with iPhone contributing 52% of total revenue.

## Risk Assessment

Key risks include China exposure and smartphone market maturation.

## Market Position & Strategy

Apple maintains strong market position with ecosystem advantages.

## Conclusion

Apple shows solid fundamentals with balanced growth profile.

## Follow-Up Questions

1. What is Apple's AI chip development timeline?
2. How will Services revenue scale?
"""


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "max_search_time_ms": 5000,
        "max_analysis_time_ms": 10000,
        "max_total_time_ms": 120000,
    }

