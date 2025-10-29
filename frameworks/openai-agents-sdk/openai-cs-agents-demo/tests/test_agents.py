"""
Comprehensive test suite for the Airline Customer Service Agent System.
"""

import os
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from src.runner import ScenarioRunner, TestScenario, ConversationTurn
from src.context import (
    AirlineAgentContext,
    create_initial_context,
    create_test_context,
    context_diff,
    generate_flight_number,
    generate_confirmation_number
)
from src.agents import (
    get_initial_agent,
    get_agent_by_name,
    list_agents,
    AGENTS,
    on_seat_booking_handoff,
    on_cancellation_handoff
)
from src.tools import (
    faq_lookup_tool,
    update_seat,
    flight_status_tool,
    baggage_tool,
    display_seat_map,
    cancel_flight,
    is_valid_flight_number
)
from src.guardrails import (
    relevance_guardrail,
    jailbreak_guardrail,
    get_guardrail_message
)


class TestContext:
    """Test context management functionality."""

    def test_create_initial_context(self):
        """Test initial context creation."""
        context = create_initial_context()
        assert isinstance(context, AirlineAgentContext)
        assert context.account_number.startswith("AC")
        assert len(context.account_number) == 14  # AC + 12 digits
        assert context.conversation_stage == "initial"

    def test_create_test_context(self):
        """Test context creation with specific values."""
        context = create_test_context(
            passenger_name="John Doe",
            flight_number="UA123",
            seat_number="15A"
        )
        assert context.passenger_name == "John Doe"
        assert context.flight_number == "UA123"
        assert context.seat_number == "15A"
        assert context.account_number.startswith("AC")

    def test_context_diff(self):
        """Test context difference detection."""
        old_context = create_initial_context()
        new_context = create_test_context(
            passenger_name="Jane Smith",
            seat_number="23B"
        )
        new_context.account_number = old_context.account_number  # Keep same account

        diff = context_diff(old_context, new_context)
        assert "passenger_name" in diff
        assert "seat_number" in diff
        assert diff["passenger_name"] == "Jane Smith"
        assert diff["seat_number"] == "23B"
        assert "account_number" not in diff  # Should not be in diff

    def test_generate_functions(self):
        """Test data generation functions."""
        flight = generate_flight_number()
        # Check that it follows the pattern we generate: 2-letter airline + number
        # Note: B6 (JetBlue) can create ambiguous patterns like B66xxx
        assert len(flight) >= 3
        assert flight[:2].isalpha() or flight[:3].isalpha()  # Has airline prefix
        assert any(c.isdigit() for c in flight)  # Has digits

        confirmation = generate_confirmation_number()
        assert len(confirmation) == 6
        assert confirmation.isalnum()


class TestAgents:
    """Test agent functionality."""

    def test_get_initial_agent(self):
        """Test getting the initial triage agent."""
        agent = get_initial_agent()
        assert agent.name == "Triage Agent"
        assert agent.handoffs is not None
        assert len(agent.handoffs) == 4  # Should handoff to 4 other agents

    def test_get_agent_by_name(self):
        """Test agent lookup by name."""
        # Exact match
        agent = get_agent_by_name("triage")
        assert agent.name == "Triage Agent"

        # Partial match
        agent = get_agent_by_name("seat")
        assert agent.name == "Seat Booking Agent"

        # Case insensitive
        agent = get_agent_by_name("FAQ")
        assert agent.name == "FAQ Agent"

        # Non-existent
        agent = get_agent_by_name("nonexistent")
        assert agent is None

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 5
        agent_names = [a["name"] for a in agents]
        assert "Triage Agent" in agent_names
        assert "Seat Booking Agent" in agent_names
        assert "Flight Status Agent" in agent_names
        assert "FAQ Agent" in agent_names
        assert "Cancellation Agent" in agent_names

    def test_handoff_hooks(self):
        """Test handoff hook functions."""
        context = create_initial_context()

        # Create a mock RunContextWrapper
        mock_wrapper = Mock()
        mock_wrapper.context = context

        # Test seat booking handoff
        asyncio.run(on_seat_booking_handoff(mock_wrapper))
        assert mock_wrapper.context.flight_number is not None
        assert mock_wrapper.context.confirmation_number is not None
        assert mock_wrapper.context.passenger_name is not None
        assert mock_wrapper.context.seat_number is not None
        assert mock_wrapper.context.conversation_stage == "seat_booking"

        # Test cancellation handoff
        context2 = create_initial_context()
        mock_wrapper2 = Mock()
        mock_wrapper2.context = context2
        asyncio.run(on_cancellation_handoff(mock_wrapper2))
        assert mock_wrapper2.context.flight_number is not None
        assert mock_wrapper2.context.confirmation_number is not None
        assert mock_wrapper2.context.conversation_stage == "cancellation"


class TestTools:
    """Test tool configuration."""

    def test_faq_lookup_tool(self):
        """Test FAQ lookup tool is properly configured."""
        # Verify tool properties
        assert faq_lookup_tool.name == "faq_lookup_tool"
        assert faq_lookup_tool.description
        assert faq_lookup_tool.params_json_schema
        assert callable(faq_lookup_tool.on_invoke_tool)

    def test_update_seat(self):
        """Test seat update tool is properly configured."""
        assert update_seat.name == "update_seat"
        assert update_seat.description
        assert update_seat.params_json_schema
        assert callable(update_seat.on_invoke_tool)

    def test_flight_status_tool(self):
        """Test flight status tool is properly configured."""
        assert flight_status_tool.name == "flight_status_tool"
        assert flight_status_tool.description
        assert flight_status_tool.params_json_schema
        assert callable(flight_status_tool.on_invoke_tool)

    def test_baggage_tool(self):
        """Test baggage tool is properly configured."""
        assert baggage_tool.name == "baggage_tool"
        assert baggage_tool.description
        assert baggage_tool.params_json_schema
        assert callable(baggage_tool.on_invoke_tool)

    def test_display_seat_map(self):
        """Test seat map display tool is properly configured."""
        assert display_seat_map.name == "display_seat_map"
        assert display_seat_map.description
        assert display_seat_map.params_json_schema
        assert callable(display_seat_map.on_invoke_tool)

    def test_cancel_flight(self):
        """Test flight cancellation tool is properly configured."""
        assert cancel_flight.name == "cancel_flight"
        assert cancel_flight.description
        assert cancel_flight.params_json_schema
        assert callable(cancel_flight.on_invoke_tool)

    def test_is_valid_flight_number(self):
        """Test flight number validation."""
        assert is_valid_flight_number("UA123")
        assert is_valid_flight_number("DL1234")
        assert is_valid_flight_number("AA1")
        assert not is_valid_flight_number("123")
        assert not is_valid_flight_number("ABCD")
        assert not is_valid_flight_number("U1234")  # Too short airline code


class TestScenarioRunner:
    """Test scenario runner functionality."""

    def test_load_scenario(self, scenario_runner, temp_scenario_file):
        """Test loading a scenario from JSON."""
        scenario = scenario_runner.load_scenario(str(temp_scenario_file))
        assert scenario.name == "Test Scenario"
        assert scenario.description == "A test scenario for unit testing"
        assert len(scenario.conversation) == 2
        assert scenario.conversation[0].user_input == "Hello"

    def test_validate_turn(self, scenario_runner):
        """Test turn validation logic."""
        turn = ConversationTurn(
            user_input="test",
            expected_agent="Triage Agent",
            expected_handoffs=["Triage Agent -> Seat Booking Agent"],
            expected_tools=["update_seat"],
            expected_context_updates=["seat_number"],
            expected_message_contains=["confirmed"]
        )

        # Test successful validation
        errors = scenario_runner.validate_turn(
            turn,
            current_agent="Triage Agent",
            handoffs=["Triage Agent -> Seat Booking Agent"],
            tools_called=["update_seat"],
            context_updates={"seat_number": "23A"},
            messages=["Your seat is confirmed"]
        )
        assert len(errors) == 0

        # Test failed validation
        errors = scenario_runner.validate_turn(
            turn,
            current_agent="Wrong Agent",
            handoffs=[],
            tools_called=[],
            context_updates={},
            messages=["Different message"]
        )
        assert len(errors) > 0
        assert any("agent" in e.lower() for e in errors)

    def test_execute_turn_with_mock(self, scenario_runner, mock_agent_response):
        """Test executing a single turn with mocked agent."""
        scenario_runner.current_agent = get_initial_agent()
        scenario_runner.context = create_initial_context()
        scenario_runner.input_items = []

        turn = ConversationTurn(
            user_input="Hello",
            expected_agent="Triage Agent"
        )

        with patch('src.runner.Runner.run', new=mock_agent_response):
            result = asyncio.run(scenario_runner.execute_turn("Hello", turn))

        assert result.user_input == "Hello"
        assert result.current_agent == "Triage Agent"
        assert len(result.messages) > 0
        assert result.validation_passed  # Should pass since we expect Triage Agent

    def test_run_scenario_with_mock(self, scenario_runner, sample_scenario_dict, mock_agent_response):
        """Test running a complete scenario with mocked responses."""
        from src.runner import TestScenario, ConversationTurn

        scenario = TestScenario(
            name=sample_scenario_dict["name"],
            description=sample_scenario_dict["description"],
            initial_context=sample_scenario_dict["initial_context"],
            conversation=[
                ConversationTurn(
                    user_input="Hello",
                    skip_validation=True  # Skip validation for mock test
                )
            ]
        )

        with patch('src.runner.Runner.run', new=mock_agent_response):
            report = asyncio.run(scenario_runner.run_scenario(scenario))

        assert report.scenario_name == "Test Scenario"
        assert report.total_turns == 1
        assert report.overall_success  # Should succeed with skip_validation

    def test_save_report(self, scenario_runner, tmp_path):
        """Test saving a scenario report."""
        from src.runner import ScenarioReport, ExecutionResult

        report = ScenarioReport(
            scenario_name="Test",
            description="Test report",
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T00:01:00",
            total_turns=1,
            successful_turns=1,
            failed_turns=0,
            turns=[
                ExecutionResult(
                    turn_number=1,
                    user_input="test",
                    current_agent="Triage Agent",
                    messages=["response"],
                    handoffs=[],
                    tools_called=[],
                    context_updates={},
                    guardrails_triggered=[],
                    validation_passed=True,
                    validation_errors=[],
                    execution_time_ms=100,
                    raw_output=None
                )
            ],
            overall_success=True,
            execution_time_ms=1000
        )

        output_file = tmp_path / "test_report.json"
        scenario_runner.save_report(report, str(output_file))

        assert output_file.exists()
        with open(output_file) as f:
            loaded = json.load(f)
        assert loaded["scenario_name"] == "Test"
        assert loaded["overall_success"] is True


class TestScenarioFiles:
    """Test actual scenario JSON files."""

    @pytest.mark.parametrize("scenario_file", [
        "seat_change.json",
        "flight_status.json",
        "cancellation.json",
        "faq_queries.json",
        "handoff_demo.json"
    ])
    def test_scenario_file_structure(self, scenario_file):
        """Test that scenario files are valid and well-structured."""
        file_path = Path(__file__).parent.parent / "src" / "scenarios" / scenario_file

        assert file_path.exists(), f"Scenario file {scenario_file} does not exist"

        with open(file_path) as f:
            data = json.load(f)

        # Check required fields
        assert "name" in data
        assert "description" in data
        assert "conversation" in data
        assert len(data["conversation"]) > 0

        # Check conversation structure
        for turn in data["conversation"]:
            assert "user" in turn
            if "expected" in turn:
                expected = turn["expected"]
                # Check that expected fields are valid
                valid_fields = {
                    "agent", "handoffs", "tools_called",
                    "context_updates", "message_contains"
                }
                assert all(k in valid_fields for k in expected.keys())

    def test_all_scenarios_loadable(self, scenario_runner, scenario_files):
        """Test that all scenario files can be loaded."""
        for scenario_file in scenario_files:
            scenario = scenario_runner.load_scenario(str(scenario_file))
            assert scenario.name is not None
            assert len(scenario.conversation) > 0


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY to be set"
    )
    def test_simple_conversation_flow(self):
        """Test a simple conversation flow with real API calls."""
        runner = ScenarioRunner(verbose=True)

        # Create a simple test scenario
        scenario = TestScenario(
            name="Simple Integration Test",
            description="Basic conversation flow test",
            initial_context={},
            conversation=[
                ConversationTurn(
                    user_input="Hello, I need help with my flight",
                    expected_agent="Triage Agent",
                    skip_validation=False
                )
            ]
        )

        report = asyncio.run(runner.run_scenario(scenario))
        assert report.total_turns == 1
        assert report.turns[0].current_agent == "Triage Agent"

    @pytest.mark.skipif(
        not os.environ.get("RUN_FULL_SCENARIOS"),
        reason="Set RUN_FULL_SCENARIOS=1 to run full scenario tests"
    )
    def test_full_scenarios(self, scenario_files):
        """Run all scenarios end-to-end (requires API key and flag)."""
        runner = ScenarioRunner(verbose=True)

        for scenario_file in scenario_files:
            print(f"\nRunning scenario: {scenario_file.name}")
            scenario = runner.load_scenario(str(scenario_file))
            report = asyncio.run(runner.run_scenario(scenario))

            # Save report
            report_file = f"test_report_{scenario_file.stem}.json"
            runner.save_report(report, report_file)

            # Basic assertions
            assert report.total_turns > 0
            print(f"Scenario {scenario.name}: {report.successful_turns}/{report.total_turns} turns passed")


class TestPerformance:
    """Performance and load tests."""

    def test_scenario_performance(self, scenario_runner, mock_agent_response, performance_thresholds):
        """Test that scenarios execute within performance thresholds."""
        scenario = TestScenario(
            name="Performance Test",
            description="Test performance",
            initial_context={},
            conversation=[
                ConversationTurn(user_input=f"Test message {i}", skip_validation=True)
                for i in range(5)
            ]
        )

        with patch('src.runner.Runner.run', new=mock_agent_response):
            report = asyncio.run(scenario_runner.run_scenario(scenario))

        # Check overall scenario time
        assert report.execution_time_ms < performance_thresholds["max_scenario_time_ms"]

        # Check individual turn times
        for turn in report.turns:
            assert turn.execution_time_ms < performance_thresholds["max_turn_time_ms"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])