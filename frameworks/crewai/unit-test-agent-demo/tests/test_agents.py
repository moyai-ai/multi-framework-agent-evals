"""
Unit tests for CrewAI agents
"""

import pytest
from src.agents import (
    create_code_analyzer_agent,
    create_test_planner_agent,
    create_test_writer_agent,
    get_agent_by_name,
    list_agents,
)


@pytest.mark.unit
class TestAgentCreation:
    """Tests for agent creation functions"""

    def test_create_code_analyzer_agent(self):
        """Test creating the code analyzer agent"""
        agent = create_code_analyzer_agent()
        assert agent is not None
        assert agent.role == "Code Analyzer"
        assert len(agent.tools) > 0

    def test_create_test_planner_agent(self):
        """Test creating the test planner agent"""
        agent = create_test_planner_agent()
        assert agent is not None
        assert agent.role == "Test Planner"
        assert len(agent.tools) > 0

    def test_create_test_writer_agent(self):
        """Test creating the test writer agent"""
        agent = create_test_writer_agent()
        assert agent is not None
        assert agent.role == "Test Writer"
        assert len(agent.tools) > 0

    def test_all_agents_have_backstory(self):
        """Test that all agents have backstories"""
        agents = [
            create_code_analyzer_agent(),
            create_test_planner_agent(),
            create_test_writer_agent(),
        ]
        for agent in agents:
            assert agent.backstory is not None
            assert len(agent.backstory) > 0

    def test_all_agents_have_goals(self):
        """Test that all agents have goals"""
        agents = [
            create_code_analyzer_agent(),
            create_test_planner_agent(),
            create_test_writer_agent(),
        ]
        for agent in agents:
            assert agent.goal is not None
            assert len(agent.goal) > 0


@pytest.mark.unit
class TestAgentRegistry:
    """Tests for agent registry functions"""

    def test_get_agent_by_exact_name(self):
        """Test getting agent by exact name"""
        agent = get_agent_by_name("code_analyzer")
        assert agent is not None
        assert agent.role == "Code Analyzer"

    def test_get_agent_by_partial_name(self):
        """Test getting agent by partial name"""
        agent = get_agent_by_name("planner")
        assert agent is not None
        assert agent.role == "Test Planner"

    def test_get_nonexistent_agent(self):
        """Test getting a nonexistent agent"""
        agent = get_agent_by_name("nonexistent_agent")
        assert agent is None

    def test_list_agents(self):
        """Test listing all agents"""
        agents = list_agents()
        assert len(agents) == 3
        assert all("name" in agent for agent in agents)
        assert all("role" in agent for agent in agents)
        assert all("description" in agent for agent in agents)

    def test_list_agents_contains_all_types(self):
        """Test that list_agents returns all agent types"""
        agents = list_agents()
        agent_names = [agent["name"] for agent in agents]
        assert "code_analyzer" in agent_names
        assert "test_planner" in agent_names
        assert "test_writer" in agent_names


@pytest.mark.unit
class TestAgentConfiguration:
    """Tests for agent configuration"""

    def test_agents_verbose_mode(self):
        """Test that agents have verbose mode enabled"""
        agents = [
            create_code_analyzer_agent(),
            create_test_planner_agent(),
            create_test_writer_agent(),
        ]
        for agent in agents:
            assert agent.verbose is True

    def test_agents_delegation_disabled(self):
        """Test that agents have delegation disabled"""
        agents = [
            create_code_analyzer_agent(),
            create_test_planner_agent(),
            create_test_writer_agent(),
        ]
        for agent in agents:
            assert agent.allow_delegation is False

    def test_code_analyzer_has_required_tools(self):
        """Test that code analyzer has the right tools"""
        agent = create_code_analyzer_agent()
        tool_names = [tool.name for tool in agent.tools]
        assert "GitHub Fetcher" in tool_names
        assert "AST Parser" in tool_names

    def test_test_planner_has_required_tools(self):
        """Test that test planner has the right tools"""
        agent = create_test_planner_agent()
        tool_names = [tool.name for tool in agent.tools]
        assert "Test Plan Generator" in tool_names

    def test_test_writer_has_required_tools(self):
        """Test that test writer has the right tools"""
        agent = create_test_writer_agent()
        tool_names = [tool.name for tool in agent.tools]
        assert "Test Code Generator" in tool_names
