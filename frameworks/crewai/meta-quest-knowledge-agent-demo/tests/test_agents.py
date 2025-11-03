"""Tests for Meta Quest Knowledge Agent."""

import pytest

from src.agents import (
    MetaQuestAgents,
    get_agent_registry,
    get_agent_by_name,
    get_initial_agent,
    list_agents,
)
from src.crew import create_crew


class TestAgentRegistry:
    """Test agent registry and lookup functionality."""

    def test_agents_registered(self, mock_env):
        """Test that agents are properly registered."""
        registry = get_agent_registry()

        assert "knowledge_expert" in registry
        assert "technical_support" in registry
        assert len(registry) == 2

    def test_get_agent_by_name_exact(self, mock_env):
        """Test getting agent by exact name."""
        agent = get_agent_by_name("knowledge_expert")

        assert agent is not None
        assert agent.role == "Meta Quest Knowledge Expert"

    def test_get_agent_by_name_partial(self, mock_env):
        """Test getting agent by partial name match."""
        agent = get_agent_by_name("knowledge")

        assert agent is not None
        assert "Knowledge" in agent.role

    def test_get_agent_by_name_not_found(self, mock_env):
        """Test getting agent with non-existent name."""
        agent = get_agent_by_name("nonexistent")

        assert agent is None

    def test_get_initial_agent(self, mock_env):
        """Test getting the initial/default agent."""
        agent = get_initial_agent()

        assert agent is not None
        assert agent.role == "Meta Quest Knowledge Expert"

    def test_list_agents(self, mock_env):
        """Test listing all agents."""
        agents = list_agents()

        assert len(agents) == 2
        assert all("name" in agent for agent in agents)
        assert all("role" in agent for agent in agents)
        assert all("goal" in agent for agent in agents)
        assert all("tools" in agent for agent in agents)


class TestAgentCreation:
    """Test agent creation and configuration."""

    def test_create_knowledge_expert(self, mock_env):
        """Test creating knowledge expert agent."""
        factory = MetaQuestAgents()
        agent = factory.knowledge_expert()

        assert agent.role == "Meta Quest Knowledge Expert"
        assert agent.tools is not None
        assert len(agent.tools) > 0
        assert agent.allow_delegation is False

    def test_create_technical_support(self, mock_env):
        """Test creating technical support agent."""
        factory = MetaQuestAgents()
        agent = factory.technical_support()

        assert agent.role == "Meta Quest Technical Support Specialist"
        assert agent.tools is not None
        assert len(agent.tools) > 0
        assert agent.allow_delegation is False

    def test_agent_with_custom_model(self, mock_env):
        """Test creating agent with custom model."""
        factory = MetaQuestAgents(model_name="gpt-4")
        agent = factory.knowledge_expert()

        assert factory.model_name == "gpt-4"

    def test_agent_with_custom_temperature(self, mock_env):
        """Test creating agent with custom temperature."""
        factory = MetaQuestAgents(temperature=0.5)
        agent = factory.knowledge_expert()

        assert factory.temperature == 0.5


class TestCrewCreation:
    """Test crew creation and configuration."""

    def test_create_crew_default(self, mock_env):
        """Test creating crew with default settings."""
        crew = create_crew()

        assert crew is not None
        assert crew.model_name == "gpt-4o"

    def test_create_crew_custom_model(self, mock_env):
        """Test creating crew with custom model."""
        crew = create_crew(model_name="gpt-4")

        assert crew.model_name == "gpt-4"

    def test_create_crew_custom_temperature(self, mock_env):
        """Test creating crew with custom temperature."""
        crew = create_crew(temperature=0.5)

        assert crew.temperature == 0.5


@pytest.mark.unit
class TestAgentTools:
    """Test that agents have the correct tools."""

    def test_knowledge_expert_has_tools(self, mock_env):
        """Test that knowledge expert has required tools."""
        factory = MetaQuestAgents()
        agent = factory.knowledge_expert()

        tool_names = [tool.name for tool in agent.tools]

        assert "search_meta_quest_docs" in tool_names
        assert "get_meta_quest_overview" in tool_names
        assert "search_specific_topic" in tool_names

    def test_technical_support_has_tools(self, mock_env):
        """Test that technical support has required tools."""
        factory = MetaQuestAgents()
        agent = factory.technical_support()

        tool_names = [tool.name for tool in agent.tools]

        assert "search_meta_quest_docs" in tool_names
        assert "get_meta_quest_overview" in tool_names
        assert "search_specific_topic" in tool_names


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests that require API access."""

    def test_answer_simple_question(self, skip_if_no_api_key, mock_knowledge_base_manager):
        """Test answering a simple question (requires API key)."""
        crew = create_crew(verbose=False)
        question = "What is Meta Quest?"

        response = crew.answer_question(question)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_answer_with_technical_support(self, skip_if_no_api_key, mock_knowledge_base_manager):
        """Test answering with technical support agent (requires API key)."""
        crew = create_crew(verbose=False)
        question = "How do I set up my Meta Quest?"

        response = crew.answer_question(question, use_technical_support=True)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_research_topic(self, skip_if_no_api_key, mock_knowledge_base_manager):
        """Test researching a topic (requires API key)."""
        crew = create_crew(verbose=False)
        topic = "controllers"

        response = crew.research_topic(topic)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
