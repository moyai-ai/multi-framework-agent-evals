"""Test that the structure is correct without requiring API key."""

import os
import pytest

# Set a dummy API key for testing imports
os.environ["OPENAI_API_KEY"] = "test-key-for-import"


def test_imports():
    """Test that all imports work correctly."""
    from src.context import BankSupportContext, create_initial_context
    from src.tools import BANK_SUPPORT_TOOLS, get_all_tools
    from src.agents import AGENTS, get_initial_agent, list_agents
    from src.runner import ScenarioRunner, TestScenario
    
    assert True  # If we get here, imports worked


def test_context_creation():
    """Test context creation."""
    from src.context import create_initial_context
    context = create_initial_context()
    assert context is not None


def test_tools():
    """Test that tools can be retrieved."""
    from src.tools import get_all_tools
    tools = get_all_tools()
    assert len(tools) > 0


def test_agents():
    """Test that agents can be listed."""
    from src.agents import list_agents
    agents = list_agents()
    assert len(agents) > 0
    
    # Verify agent structure
    for agent_info in agents:
        assert "name" in agent_info
        assert "tools" in agent_info