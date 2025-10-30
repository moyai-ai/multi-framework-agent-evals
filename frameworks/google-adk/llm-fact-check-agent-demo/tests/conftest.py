"""
Pytest configuration and fixtures for LLM fact-checking agent tests.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents import llm_fact_check_agent, critic_agent, reviser_agent


@pytest.fixture
def mock_google_search():
    """Mock the google_search tool."""
    mock = AsyncMock()
    mock.return_value = {
        "results": [
            {
                "title": "Test Result",
                "snippet": "This is a test search result",
                "link": "https://example.com"
            }
        ]
    }
    return mock


@pytest.fixture
def mock_runner():
    """Mock the InMemoryRunner for testing."""
    runner = MagicMock()
    runner.session_service.create_session = AsyncMock(
        return_value=MagicMock(user_id="test_user", id="test_session")
    )

    # Create a proper async generator mock
    class AsyncIteratorMock:
        def __init__(self):
            self.items = []
            self.index = 0

        def add_event(self, text, tools=None):
            event = MagicMock()
            event.content.parts = [MagicMock(text=text)]
            event.metadata = {"tools": tools} if tools else {}
            self.items.append(event)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.index < len(self.items):
                item = self.items[self.index]
                self.index += 1
                return item
            raise StopAsyncIteration

    async_iter = AsyncIteratorMock()
    async_iter.add_event("Test response", ["google_search"])
    runner.run_async = MagicMock(return_value=async_iter)
    runner.app_name = "test_app"
    return runner


@pytest.fixture
def scenario_files():
    """Get paths to test scenario files."""
    scenario_dir = Path(__file__).parent.parent / "src" / "scenarios"
    return {
        "accurate": scenario_dir / "accurate_facts.json",
        "inaccurate": scenario_dir / "inaccurate_facts.json",
        "mixed": scenario_dir / "mixed_accuracy.json",
        "disputed": scenario_dir / "disputed_claims.json",
    }


@pytest.fixture
def sample_qa_pairs():
    """Sample Q&A pairs for testing."""
    return {
        "accurate": "Q: Who was the first president of the US? A: George Washington was the first president of the United States.",
        "inaccurate": "Q: What is the capital of France? A: The capital of France is Berlin.",
        "mixed": "Q: Tell me about Earth. A: Earth is the third planet from the sun and the largest planet in the solar system.",
        "disputed": "Q: When was Shakespeare born? A: Shakespeare was born on April 23, 1564.",
    }


@pytest.fixture
def api_key():
    """Check if Google API key is available."""
    return os.environ.get('GOOGLE_API_KEY') or os.environ.get('GOOGLE_CLOUD_PROJECT')


@pytest.fixture
def skip_if_no_api_key(api_key):
    """Skip test if no API key is available."""
    if not api_key:
        pytest.skip("No Google API key or project found. Set GOOGLE_API_KEY or GOOGLE_CLOUD_PROJECT to run integration tests.")


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing callbacks."""
    class MockPart:
        def __init__(self, text):
            self.text = text

    class MockContent:
        def __init__(self, text):
            self.parts = [MockPart(text)]

    class MockGroundingChunk:
        def __init__(self):
            self.retrieved_context = None
            self.web = MagicMock(
                title="Test Title",
                uri="https://example.com"
            )

    class MockGroundingMetadata:
        def __init__(self):
            self.grounding_chunks = [MockGroundingChunk()]

    class MockLlmResponse:
        def __init__(self, text):
            self.content = MockContent(text)
            self.grounding_metadata = MockGroundingMetadata()

    return MockLlmResponse


@pytest.fixture
def mock_callback_context():
    """Mock callback context for testing."""
    return MagicMock()