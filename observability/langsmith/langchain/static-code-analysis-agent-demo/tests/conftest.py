"""
Test configuration and fixtures for Static Code Analysis Agent tests.
"""

import pytest
import asyncio
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context import Config, AnalysisContext, create_test_context
from src.agent import create_agent
from src.runner import ScenarioRunner, Scenario, ConversationTurn


@pytest.fixture
def test_config():
    """Create a test configuration."""
    config = Config()
    config.OPENAI_API_KEY = "test-api-key"
    config.MODEL_NAME = "gpt-4-turbo-preview"
    config.DEBUG = True
    return config


@pytest.fixture
def test_context():
    """Create a test analysis context."""
    return create_test_context()


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    with patch("src.agent.graph.ChatOpenAI") as mock_client:
        mock_instance = Mock()
        mock_instance.invoke = Mock(return_value=Mock(content="Test response"))
        mock_instance.bind_tools = Mock(return_value=mock_instance)
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub MCP client."""
    with patch("src.tools.github_tools.GitHubMCPClient") as mock_client:
        mock_instance = Mock()
        mock_instance.execute_mcp_function = AsyncMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_vulnerable_code():
    """Sample vulnerable Python code for testing."""
    return '''import sqlite3
import os

def get_user(user_id):
    """Get user from database - VULNERABLE TO SQL INJECTION"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

# Hardcoded secret
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

def execute_command(cmd):
    """Execute system command - VULNERABLE TO COMMAND INJECTION"""
    # Command injection vulnerability
    result = os.system(cmd)
    return result
'''


@pytest.fixture
def sample_quality_issues_code():
    """Sample code with quality issues for testing."""
    return '''def process_all_data(data_list, config, user_settings, cache, db_connection):
    # This function is way too long
    results = []
    errors = []

    # TODO: Refactor this function
    for item in data_list:
        try:
            if item['type'] == 'user':
                if item['age'] > 18:
                    if item['country'] == 'US':
                        if item['premium']:
                            # Deep nesting
                            result = process_premium(item)
                        else:
                            result = process_standard(item)
                    else:
                        result = process_international(item)
                else:
                    result = process_minor(item)

            # Magic number
            if item['score'] > 86400:
                item['special'] = True

            results.append(result)

        except Exception:
            # Empty exception handler
            pass

    return results
'''


@pytest.fixture
def sample_dependencies():
    """Sample dependencies file with vulnerabilities."""
    return """flask==1.1.2
django==2.2.10
requests==2.20.0
pyyaml==5.1
sqlalchemy==1.3.0
pytest==4.6.2
"""


@pytest.fixture
def test_scenario():
    """Create a test scenario."""
    return Scenario(
        name="Test Security Analysis",
        description="Test scenario for security analysis",
        initial_context={
            "repository_url": "https://github.com/test/repo",
            "analysis_type": "security"
        },
        conversation=[
            ConversationTurn(
                user="Analyze the security of this repository",
                expected={
                    "actions": ["fetch_repository_info"],
                    "message_contains": ["security", "analysis"]
                }
            )
        ],
        metadata={"test": True}
    )


@pytest.fixture
def scenario_runner(test_config):
    """Create a scenario runner."""
    return ScenarioRunner(verbose=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Environment variable fixtures
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("DEBUG", "true")
    # Force mock OpenGrep for all unit tests
    monkeypatch.setenv("USE_MOCK_OPENGREP", "true")
    # Explicitly disable LangSmith tracing for all unit tests
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGSMITH_API_KEY", "")
    # Remove any existing LangSmith environment variables that might enable tracing
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)
    monkeypatch.delenv("LANGSMITH_ENDPOINT", raising=False)
    monkeypatch.delenv("LANGSMITH_WORKSPACE_ID", raising=False)