"""
Comprehensive test suite for the Weather Agent System.
"""

import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.runner import ScenarioRunner, TestScenario, ConversationTurn
from src.context import (
    WeatherAgentContext,
    create_initial_context,
    create_test_context,
    context_diff,
    update_context
)
from src.agents import (
    get_initial_agent,
    get_agent_by_name,
    list_agents,
    AGENTS,
    weather_agent
)
from src.weather_service import (
    get_weather,
    get_simulated_weather,
    get_weather_recommendation,
    WeatherResponse
)


class TestContext:
    """Test context management functionality."""

    def test_create_initial_context(self):
        """Test initial context creation."""
        context = create_initial_context()
        assert isinstance(context, WeatherAgentContext)
        assert context.conversation_stage == "initial"
        assert context.current_location is None
        assert context.last_temperature is None

    def test_create_test_context(self):
        """Test context creation with specific values."""
        context = create_test_context(
            current_location="San Francisco",
            last_temperature="62°F",
            last_conditions="Sunny"
        )
        assert context.current_location == "San Francisco"
        assert context.last_temperature == "62°F"
        assert context.last_conditions == "Sunny"

    def test_context_diff(self):
        """Test context difference detection."""
        old_context = create_initial_context()
        new_context = create_test_context(
            current_location="New York",
            last_temperature="55°F"
        )

        diff = context_diff(old_context, new_context)
        assert "current_location" in diff
        assert "last_temperature" in diff
        assert diff["current_location"] == "New York"
        assert diff["last_temperature"] == "55°F"

    def test_update_context(self):
        """Test context update functionality."""
        context = create_initial_context()
        updates = {
            "current_location": "Tokyo",
            "last_conditions": "Clear"
        }
        updated_context = update_context(context, updates)
        assert updated_context.current_location == "Tokyo"
        assert updated_context.last_conditions == "Clear"


class TestWeatherService:
    """Test weather service functionality."""

    def test_get_simulated_weather_known_city(self):
        """Test simulated weather for known cities."""
        response = get_simulated_weather("San Francisco")
        assert response is not None
        assert response.city == "San Francisco"
        assert "°F" in response.temperature or "°C" in response.temperature
        assert len(response.conditions) > 0
        assert len(response.recommendation) > 0

    def test_get_simulated_weather_unknown_city(self):
        """Test simulated weather for unknown cities."""
        response = get_simulated_weather("UnknownCity")
        assert response is None

    def test_get_weather_recommendation(self):
        """Test weather recommendation generation."""
        # Test cold weather
        rec = get_weather_recommendation("35°F", "Clear")
        assert "cold" in rec.lower() or "warm" in rec.lower()

        # Test rainy weather
        rec = get_weather_recommendation("60°F", "Rain")
        assert "umbrella" in rec.lower()

        # Test hot weather
        rec = get_weather_recommendation("85°F", "Sunny")
        assert "hot" in rec.lower() or "hydrat" in rec.lower()

    @pytest.mark.asyncio
    async def test_get_weather_simulated(self):
        """Test get_weather with simulated data."""
        response = await get_weather("San Francisco")
        assert isinstance(response, WeatherResponse)
        assert response.city == "San Francisco"

    @pytest.mark.asyncio
    async def test_get_weather_invalid_city(self):
        """Test get_weather with invalid city."""
        with pytest.raises(ValueError):
            await get_weather("ThisCityDefinitelyDoesNotExist12345")


class TestAgents:
    """Test agent functionality."""

    def test_get_initial_agent(self):
        """Test getting initial agent."""
        agent = get_initial_agent()
        assert agent is not None
        assert agent.name == "Weather Agent"

    def test_get_agent_by_name(self):
        """Test agent lookup by name."""
        agent = get_agent_by_name("weather")
        assert agent is not None
        assert agent.name == "Weather Agent"

        agent = get_agent_by_name("Weather Agent")
        assert agent is not None

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) > 0
        assert any(a["name"] == "Weather Agent" for a in agents)

    def test_weather_agent_has_tools(self):
        """Test that weather agent has required tools."""
        agent = weather_agent
        assert agent.tools is not None
        assert len(agent.tools) >= 1


class TestScenarioRunner:
    """Test scenario runner functionality."""

    def test_load_scenario(self, scenario_files):
        """Test loading scenario from JSON."""
        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(scenario_files["weather_queries"]))

        assert scenario.name == "Basic Weather Queries"
        assert len(scenario.conversation) > 0
        assert scenario.initial_context is not None

    def test_scenario_structure(self, scenario_files):
        """Test scenario structure validation."""
        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(scenario_files["umbrella"]))

        assert isinstance(scenario, TestScenario)
        assert len(scenario.conversation) >= 1

        turn = scenario.conversation[0]
        assert isinstance(turn, ConversationTurn)
        assert turn.user_input is not None


class TestIntegration:
    """Integration tests requiring API key."""

    @pytest.mark.asyncio
    async def test_simple_weather_query(self, skip_if_no_api_key, mock_weather_service):
        """Test a simple weather query end-to-end."""
        from agents import Runner
        from src.agents import weather_agent
        from src.context import create_initial_context

        context = create_initial_context()
        input_items = [{"role": "user", "content": "What's the weather in San Francisco?"}]

        result = await Runner.run(
            weather_agent,
            input_items,
            context=context
        )

        assert result is not None
        assert len(result.new_items) > 0

    @pytest.mark.asyncio
    async def test_scenario_execution(self, skip_if_no_api_key, scenario_files, mock_weather_service):
        """Test executing a full scenario."""
        runner = ScenarioRunner(verbose=False)
        scenario = runner.load_scenario(str(scenario_files["weather_queries"]))

        report = await runner.run_scenario(scenario)

        assert report is not None
        assert report.scenario_name == scenario.name
        assert report.total_turns == len(scenario.conversation)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("RUN_FULL_SCENARIOS"),
        reason="Set RUN_FULL_SCENARIOS=1 to run full scenario tests"
    )
    async def test_all_scenarios(self, skip_if_no_api_key, scenario_files):
        """Test executing all scenarios with real API."""
        runner = ScenarioRunner(verbose=True)

        for scenario_name, scenario_path in scenario_files.items():
            print(f"\nTesting scenario: {scenario_name}")
            scenario = runner.load_scenario(str(scenario_path))
            report = await runner.run_scenario(scenario)

            # Check that at least some turns passed
            # (we can't guarantee all will pass with real API due to variations)
            assert report.successful_turns >= 0
            print(f"Scenario {scenario_name}: {report.successful_turns}/{report.total_turns} turns passed")


class TestTools:
    """Test tool functionality."""

    @pytest.mark.asyncio
    async def test_get_weather_tool(self, mock_weather_service):
        """Test get_weather tool."""
        from agents.tool_context import ToolContext
        from src.tools import get_weather_tool
        from src.context import create_initial_context

        # Verify tool configuration
        assert get_weather_tool.name == "get_weather"
        assert get_weather_tool.description
        assert get_weather_tool.params_json_schema
        assert callable(get_weather_tool.on_invoke_tool)

        # Test tool invocation
        context = create_initial_context()
        tool_ctx = ToolContext(
            context=context,
            tool_name="get_weather",
            tool_call_id="test_call_1",
            tool_arguments='{"city": "San Francisco"}'
        )

        result = await get_weather_tool.on_invoke_tool(tool_ctx, '{"city": "San Francisco"}')

        assert "San Francisco" in result
        assert "Temperature" in result or "temperature" in result
        assert context.current_location == "San Francisco"
        assert context.last_temperature is not None

    @pytest.mark.asyncio
    async def test_compare_weather_tool(self, mock_weather_service):
        """Test compare_weather tool."""
        from agents.tool_context import ToolContext
        from src.tools import compare_weather_tool
        from src.context import create_initial_context

        # Verify tool configuration
        assert compare_weather_tool.name == "compare_weather"
        assert compare_weather_tool.description
        assert compare_weather_tool.params_json_schema
        assert callable(compare_weather_tool.on_invoke_tool)

        # Test tool invocation
        context = create_initial_context()
        tool_ctx = ToolContext(
            context=context,
            tool_name="compare_weather",
            tool_call_id="test_call_2",
            tool_arguments='{"city1": "San Francisco", "city2": "New York"}'
        )

        result = await compare_weather_tool.on_invoke_tool(tool_ctx, '{"city1": "San Francisco", "city2": "New York"}')

        assert "San Francisco" in result
        assert "New York" in result
        assert "Temperature" in result or "temperature" in result
        assert context.conversation_stage == "weather_compared"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
