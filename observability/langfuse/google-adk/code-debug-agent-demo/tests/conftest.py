"""Test configuration for Code Debug Agent."""

import pytest
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()

# Disable Langfuse tracing during unit tests
os.environ["DISABLE_LANGFUSE_TRACING"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir():
    """Get the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing."""
    return os.getenv("GOOGLE_API_KEY", "test-api-key")


@pytest.fixture
def sample_error_messages():
    """Provide sample error messages for testing."""
    return {
        "python_import": "ImportError: No module named 'pandas'",
        "javascript_type": "TypeError: Cannot read property 'map' of undefined",
        "python_attribute": "AttributeError: 'NoneType' object has no attribute 'split'",
        "node_module": "Error: Cannot find module 'express'",
        "typescript_type": "Type 'string' is not assignable to type 'number'",
    }


@pytest.fixture
def sample_stack_exchange_response():
    """Mock Stack Exchange API response."""
    return {
        "success": True,
        "query": "ImportError pandas",
        "results": [
            {
                "question_id": 12345,
                "title": "ImportError: No module named pandas",
                "link": "https://stackoverflow.com/questions/12345",
                "score": 42,
                "answer_count": 3,
                "is_answered": True,
                "has_accepted_answer": True,
                "tags": ["python", "pandas", "import"],
                "body": "I'm trying to import pandas but getting an error...",
                "top_answer": {
                    "answer_id": 67890,
                    "score": 55,
                    "is_accepted": True,
                    "body": "You need to install pandas using pip: pip install pandas",
                }
            }
        ]
    }