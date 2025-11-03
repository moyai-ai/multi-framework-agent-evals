"""Pytest configuration and fixtures for Meta Quest Knowledge Agent tests."""

import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-key-12345",
        "MODEL_NAME": "gpt-4o",
        "TEMPERATURE": "0.7",
        "CREW_VERBOSE": "false",
        "MAX_ITERATIONS": "5",
        "KNOWLEDGE_DIR": "./knowledge",
        "OUTPUT_DIR": "./results/output",
        "LOG_LEVEL": "ERROR",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture
def api_key():
    """Get the OpenAI API key from environment."""
    return os.environ.get("OPENAI_API_KEY")


@pytest.fixture
def skip_if_no_api_key(api_key):
    """Skip test if no API key is available."""
    if not api_key or api_key.startswith("test-"):
        pytest.skip("OpenAI API key not set - skipping integration test")


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "What is Meta Quest?"


@pytest.fixture
def sample_questions():
    """Multiple sample questions for testing."""
    return [
        "What is Meta Quest?",
        "How do I set up my Meta Quest headset?",
        "What games are available for Meta Quest?",
    ]


@pytest.fixture
def sample_scenario():
    """Sample scenario for testing."""
    return {
        "name": "Test Scenario",
        "description": "A test scenario",
        "conversation": [
            {
                "user": "What is Meta Quest?",
                "expected": {
                    "message_contains": ["Meta", "Quest"],
                },
            },
        ],
    }


@pytest.fixture
def mock_vector_store():
    """Mock FAISS vector store for testing."""
    mock_store = MagicMock()

    # Mock similarity search results
    mock_doc = Mock()
    mock_doc.page_content = "Meta Quest is a virtual reality headset."
    mock_store.similarity_search.return_value = [mock_doc]

    return mock_store


@pytest.fixture
def mock_knowledge_base_manager(monkeypatch, mock_vector_store):
    """Mock KnowledgeBaseManager for testing."""
    from src.tools import KnowledgeBaseManager

    # Create mock manager
    mock_manager = Mock(spec=KnowledgeBaseManager)
    mock_manager.vector_store = mock_vector_store
    mock_manager.search.return_value = [
        "Meta Quest is a virtual reality headset.",
        "It features standalone VR gaming.",
    ]

    # Patch the get_knowledge_base_manager function
    def mock_get_kb_manager():
        return mock_manager

    monkeypatch.setattr("src.tools.get_knowledge_base_manager", mock_get_kb_manager)

    return mock_manager


@pytest.fixture
def knowledge_dir(tmp_path):
    """Create a temporary knowledge directory for testing."""
    kb_dir = tmp_path / "knowledge"
    kb_dir.mkdir()
    return kb_dir


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return """
    Meta Quest 3 User Guide

    What is Meta Quest?
    Meta Quest is a line of virtual reality headsets developed by Meta.

    Key Features:
    - Standalone VR gaming
    - Hand tracking
    - Mixed reality capabilities
    - Access to thousands of apps and games

    Setup Instructions:
    1. Charge your headset
    2. Download the Meta Quest app on your phone
    3. Follow the in-app setup process
    4. Create or log in to your Meta account
    """


@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    return out_dir
