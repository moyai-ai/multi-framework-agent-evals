"""
Test Configuration and Fixtures

Provides pytest fixtures and configuration for testing.
"""

import os
import pytest
import asyncio
from typing import Generator
from unittest.mock import Mock, AsyncMock, MagicMock

from src.database import DatabaseManager, init_database
from src.context import ConversationContext, context_manager
from src.agents import OrchestratorAgent


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create a test database for the session."""
    # Use in-memory SQLite for tests
    test_db_url = "sqlite:///:memory:"
    db_manager = DatabaseManager(test_db_url)
    db_manager.create_tables()

    # Load sample data
    with open("src/data/seed_data.sql", "r") as f:
        sql_commands = f.read()
        # Execute commands one by one (SQLite doesn't support multi-statement)
        for command in sql_commands.split(";"):
            command = command.strip()
            if command and not command.startswith("--"):
                try:
                    db_manager.execute_raw_sql(command)
                except Exception as e:
                    print(f"Skipping command due to error: {e}")

    yield db_manager

    # Cleanup
    db_manager.drop_tables()


@pytest.fixture
def db_manager(test_db):
    """Provide database manager for tests."""
    return test_db


@pytest.fixture
def sample_context():
    """Create a sample conversation context."""
    context = ConversationContext(
        session_id="test_session_123",
        original_request="Show me the top 5 customers by order value"
    )
    return context


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing agents without API calls."""
    mock = MagicMock()
    mock.invoke = AsyncMock(return_value={
        "output": "Test response",
        "intermediate_steps": []
    })
    return mock


@pytest.fixture
def orchestrator_agent():
    """Create an orchestrator agent for testing."""
    # Mock the OpenAI API to avoid actual API calls in tests
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("OPENAI_API_KEY", "test_key")
        agent = OrchestratorAgent()
        return agent


@pytest.fixture
def sample_query_results():
    """Provide sample query results for testing."""
    return [
        {"id": 1, "name": "Alice Johnson", "total_orders": 3, "total_spent": 1989.92},
        {"id": 2, "name": "Bob Smith", "total_orders": 3, "total_spent": 1259.94},
        {"id": 4, "name": "David Brown", "total_orders": 2, "total_spent": 1989.95},
        {"id": 5, "name": "Emma Davis", "total_orders": 2, "total_spent": 1879.93},
        {"id": 3, "name": "Carol Williams", "total_orders": 3, "total_spent": 1749.94},
    ]


@pytest.fixture
def sample_schema_info():
    """Provide sample schema information."""
    return {
        "customers": {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "name", "type": "VARCHAR(100)", "nullable": False, "primary_key": False},
                {"name": "email", "type": "VARCHAR(100)", "nullable": False, "primary_key": False},
            ],
            "foreign_keys": []
        },
        "orders": {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "customer_id", "type": "INTEGER", "nullable": False, "primary_key": False},
                {"name": "total_amount", "type": "FLOAT", "nullable": True, "primary_key": False},
            ],
            "foreign_keys": [
                {"column": "customer_id", "references": "customers.id"}
            ]
        }
    }


@pytest.fixture(autouse=True)
def reset_context_manager():
    """Reset the global context manager before each test."""
    context_manager.contexts.clear()
    context_manager.active_context_id = None
    yield
    context_manager.contexts.clear()
    context_manager.active_context_id = None