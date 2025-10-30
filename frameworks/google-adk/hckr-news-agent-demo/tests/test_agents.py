"""Tests for Hacker News agents."""

import pytest
from unittest.mock import MagicMock, patch

from src.agents import (
    AGENTS,
    get_agent_by_name,
    get_initial_agent,
    list_agents,
    get_agent_for_query
)


class TestAgentRegistry:
    """Test agent registry and lookup functions."""

    def test_agents_registered(self):
        """Verify all expected agents are registered."""
        expected_agents = [
            "hacker_news_agent",
            "search_agent",
            "trending_agent",
            "user_agent",
            "comment_agent",
            "multi_analysis_agent"
        ]

        for agent_name in expected_agents:
            assert agent_name in AGENTS, f"Agent '{agent_name}' not found in registry"

    def test_get_agent_by_exact_name(self):
        """Test getting agent by exact name."""
        agent = get_agent_by_name("search_agent")
        assert agent is not None
        assert agent.name == "search_agent"

    def test_get_agent_by_partial_name(self):
        """Test getting agent by partial name match."""
        agent = get_agent_by_name("search")
        assert agent is not None
        assert "search" in agent.name.lower()

    def test_get_agent_not_found(self):
        """Test getting non-existent agent returns None."""
        agent = get_agent_by_name("nonexistent_agent")
        assert agent is None

    def test_get_initial_agent(self):
        """Test getting the initial/default agent."""
        agent = get_initial_agent()
        assert agent is not None
        assert agent.name == "hacker_news_agent"

    def test_list_agents(self):
        """Test listing all agents."""
        agents_list = list_agents()
        assert len(agents_list) == len(AGENTS)

        for agent_info in agents_list:
            assert "name" in agent_info
            assert "description" in agent_info
            assert "model" in agent_info
            assert "tools" in agent_info


class TestAgentRouting:
    """Test query-based agent routing."""

    def test_route_to_trending_agent(self):
        """Test routing trending queries to trending agent."""
        queries = [
            "What's trending on HN?",
            "Show me popular stories",
            "Get top posts",
            "What's hot today?"
        ]

        for query in queries:
            agent = get_agent_for_query(query)
            assert agent.name == "trending_agent", f"Query '{query}' not routed to trending_agent"

    def test_route_to_search_agent(self):
        """Test routing search queries to search agent."""
        queries = [
            "Search for Python tutorials",
            "Find stories about AI",
            "Look for startup news"
        ]

        for query in queries:
            agent = get_agent_for_query(query)
            assert agent.name == "search_agent", f"Query '{query}' not routed to search_agent"

    def test_route_to_user_agent(self):
        """Test routing user queries to user agent."""
        queries = [
            "Tell me about user pg",
            "Show pg's profile",
            "What's pg's karma?",
            "Who is dang?"
        ]

        for query in queries:
            agent = get_agent_for_query(query)
            assert agent.name == "user_agent", f"Query '{query}' not routed to user_agent"

    def test_route_to_comment_agent(self):
        """Test routing comment queries to comment agent."""
        queries = [
            "Analyze comments for story 123",
            "What's the discussion about?",
            "Show comment thread",
            "What's the sentiment?"
        ]

        for query in queries:
            agent = get_agent_for_query(query)
            assert agent.name == "comment_agent", f"Query '{query}' not routed to comment_agent"

    def test_default_routing(self):
        """Test default routing for ambiguous queries."""
        query = "Tell me something interesting"
        agent = get_agent_for_query(query)
        assert agent.name == "hacker_news_agent"


class TestAgentConfiguration:
    """Test agent configuration and properties."""

    def test_agent_models(self):
        """Test that agents use correct models."""
        for name, agent in AGENTS.items():
            if name != "multi_analysis_agent":  # Sequential agent doesn't have model attribute
                assert hasattr(agent, "model")
                assert agent.model == "gemini-2.0-flash"

    def test_agent_tools(self):
        """Test that agents have appropriate tools."""
        # Main agent should have all tools
        main_agent = AGENTS["hacker_news_agent"]
        assert hasattr(main_agent, "tools")
        assert len(main_agent.tools) == 4

        # Specialized agents should have specific tools
        search_agent = AGENTS["search_agent"]
        assert len(search_agent.tools) == 1

    def test_agent_descriptions(self):
        """Test that all agents have descriptions."""
        for name, agent in AGENTS.items():
            assert hasattr(agent, "description") or hasattr(agent, "_description")
            desc = getattr(agent, "description", None) or getattr(agent, "_description", None)
            assert desc is not None
            assert len(desc) > 0