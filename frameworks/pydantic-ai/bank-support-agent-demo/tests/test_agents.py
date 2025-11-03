"""Tests for bank support agents."""

import pytest
from src.agents import (
    create_bank_support_agent,
    create_fraud_specialist_agent,
    create_account_specialist_agent,
    get_agent_by_name,
    get_initial_agent,
    list_agents,
    get_agent_for_request_type,
    get_agent_tools,
    AGENTS,
)
from src.context import BankSupportContext


class TestAgentCreation:
    """Test agent creation and configuration."""

    def test_create_bank_support_agent(self):
        """Test creating bank support agent."""
        agent = create_bank_support_agent()
        assert agent is not None
        assert agent.name == "Bank Support Agent"
        tools = get_agent_tools(agent) if not hasattr(agent, 'tools') else (agent.tools or [])
        assert len(tools) > 0

    def test_create_fraud_specialist_agent(self):
        """Test creating fraud specialist agent."""
        agent = create_fraud_specialist_agent()
        assert agent is not None
        assert agent.name == "Fraud Specialist Agent"
        # Fraud specialist has fewer tools
        bank_support = create_bank_support_agent()
        agent_tools = get_agent_tools(agent) if not hasattr(agent, 'tools') else (agent.tools or [])
        bank_tools = get_agent_tools(bank_support) if not hasattr(bank_support, 'tools') else (bank_support.tools or [])
        assert len(agent_tools) < len(bank_tools)

    def test_create_account_specialist_agent(self):
        """Test creating account specialist agent."""
        agent = create_account_specialist_agent()
        assert agent is not None
        assert agent.name == "Account Specialist Agent"
        tools = get_agent_tools(agent) if not hasattr(agent, 'tools') else (agent.tools or [])
        assert len(tools) > 0

    def test_agent_with_custom_model(self):
        """Test creating agent with custom model."""
        agent = create_bank_support_agent(
            model_name="gpt-3.5-turbo",
            temperature=0.5
        )
        assert agent is not None


class TestAgentRegistry:
    """Test agent registry functions."""

    def test_agents_registry(self):
        """Test AGENT_FACTORIES registry contains all agent factories."""
        from src.agents import AGENT_FACTORIES
        assert "bank_support" in AGENT_FACTORIES
        assert "fraud_specialist" in AGENT_FACTORIES
        assert "account_specialist" in AGENT_FACTORIES
        assert len(AGENT_FACTORIES) >= 3

    def test_get_agent_by_exact_name(self):
        """Test getting agent by exact name."""
        agent = get_agent_by_name("bank_support")
        assert agent is not None
        assert agent.name == "Bank Support Agent"

    def test_get_agent_by_partial_name(self):
        """Test getting agent by partial name."""
        agent = get_agent_by_name("fraud")
        assert agent is not None
        assert agent.name == "Fraud Specialist Agent"

        agent = get_agent_by_name("account")
        assert agent is not None
        assert agent.name == "Account Specialist Agent"

    def test_get_agent_by_name_not_found(self):
        """Test getting non-existent agent."""
        agent = get_agent_by_name("nonexistent_agent")
        assert agent is None

    def test_get_initial_agent(self):
        """Test getting initial entry point agent."""
        agent = get_initial_agent()
        assert agent is not None
        assert agent.name == "Bank Support Agent"

    def test_list_agents(self):
        """Test listing all available agents."""
        agents_list = list_agents()
        assert len(agents_list) >= 3

        # Check structure of agent info
        for agent_info in agents_list:
            assert "key" in agent_info
            assert "name" in agent_info
            assert "tools" in agent_info
            assert "model" in agent_info

        # Check specific agents are listed
        agent_keys = [a["key"] for a in agents_list]
        assert "bank_support" in agent_keys
        assert "fraud_specialist" in agent_keys
        assert "account_specialist" in agent_keys


class TestAgentRouting:
    """Test agent routing based on request type."""

    def test_route_to_fraud_specialist(self):
        """Test routing fraud-related requests."""
        fraud_requests = [
            "I see suspicious activity",
            "unauthorized transaction",
            "my card was stolen",
            "potential fraud alert",
            "scam attempt"
        ]

        for request in fraud_requests:
            agent = get_agent_for_request_type(request)
            assert agent.name == "Fraud Specialist Agent"

    def test_route_to_account_specialist(self):
        """Test routing account-related requests."""
        account_requests = [
            "check my balance",
            "transfer money",
            "view statement",
            "recent transactions"
        ]

        for request in account_requests:
            agent = get_agent_for_request_type(request)
            assert agent.name == "Account Specialist Agent"

    def test_route_to_default_agent(self):
        """Test routing general requests to default agent."""
        general_requests = [
            "I need help",
            "customer service",
            "general inquiry",
            "speak to someone"
        ]

        for request in general_requests:
            agent = get_agent_for_request_type(request)
            assert agent.name == "Bank Support Agent"


class TestAgentTools:
    """Test agent tool configuration."""

    def test_bank_support_agent_tools(self):
        """Test bank support agent has all tools."""
        agent = get_agent_by_name("bank_support")
        tools = get_agent_tools(agent) if not hasattr(agent, 'tools') else (agent.tools or [])
        tool_names = [t.__name__ for t in tools if hasattr(t, '__name__')]

        expected_tools = [
            "check_authentication_status",
            "authenticate_customer",
            "get_account_balance",
            "get_recent_transactions",
            "transfer_funds",
            "create_support_ticket",
            "check_fraud_alert",
            "update_contact_info"
        ]

        for tool in expected_tools:
            assert tool in tool_names

    def test_fraud_specialist_tools(self):
        """Test fraud specialist has specific tools."""
        agent = get_agent_by_name("fraud_specialist")
        tools = get_agent_tools(agent) if not hasattr(agent, 'tools') else (agent.tools or [])
        tool_names = [t.__name__ for t in tools if hasattr(t, '__name__')]

        # Should have fraud-related tools
        assert "check_fraud_alert" in tool_names
        assert "authenticate_customer" in tool_names
        assert "create_support_ticket" in tool_names

        # Should NOT have account management tools
        assert "transfer_funds" not in tool_names
        assert "update_contact_info" not in tool_names

    def test_account_specialist_tools(self):
        """Test account specialist has account tools."""
        agent = get_agent_by_name("account_specialist")
        tools = get_agent_tools(agent) if not hasattr(agent, 'tools') else (agent.tools or [])
        tool_names = [t.__name__ for t in tools if hasattr(t, '__name__')]

        # Should have account-related tools
        assert "get_account_balance" in tool_names
        assert "get_recent_transactions" in tool_names
        assert "transfer_funds" in tool_names

        # Should NOT have fraud tools
        assert "check_fraud_alert" not in tool_names


@pytest.mark.integration
class TestAgentExecution:
    """Integration tests for agent execution."""

    @pytest.mark.asyncio
    async def test_agent_responds_to_greeting(self, skip_if_no_api_key, initial_context):
        """Test agent responds to greeting."""
        agent = get_initial_agent()
        result = await agent.run(
            "Hello, I need help with my account",
            deps=initial_context
        )
        assert result.output is not None
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_agent_context_dependency(self, skip_if_no_api_key, test_context):
        """Test agent uses context properly."""
        agent = get_initial_agent()
        result = await agent.run(
            "What's my account balance?",
            deps=test_context
        )
        assert result.output is not None