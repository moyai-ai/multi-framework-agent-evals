"""Tests for scenario runner."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.runner import (
    ConversationTurn,
    TestScenario,
    TurnResult,
    ScenarioReport,
    ScenarioRunner,
)
from src.context import create_initial_context, create_test_context


class TestDataModels:
    """Test runner data models."""

    def test_conversation_turn(self):
        """Test ConversationTurn model."""
        turn = ConversationTurn(
            user_input="Check my balance",
            expected_agent="bank_support",
            expected_tools=["get_account_balance"],
            expected_message_contains=["balance", "$"]
        )
        assert turn.user_input == "Check my balance"
        assert turn.expected_agent == "bank_support"
        assert len(turn.expected_tools) == 1
        assert turn.skip_validation is False

    def test_test_scenario(self):
        """Test TestScenario model."""
        scenario = TestScenario(
            name="Test Scenario",
            description="A test scenario",
            initial_context={"authenticated": False},
            conversation=[
                ConversationTurn(user_input="Hello")
            ],
            metadata={"priority": "high"}
        )
        assert scenario.name == "Test Scenario"
        assert len(scenario.conversation) == 1
        assert scenario.metadata["priority"] == "high"

    def test_turn_result(self):
        """Test TurnResult model."""
        context_before = create_initial_context()
        context_after = create_test_context()

        result = TurnResult(
            user_input="Test input",
            agent_response="Test response",
            tools_called=["tool1", "tool2"],
            context_before=context_before,
            context_after=context_after,
            context_changes={"authenticated": {"old": False, "new": True}},
            execution_time=1.5,
            errors=[]
        )
        assert result.user_input == "Test input"
        assert len(result.tools_called) == 2
        assert result.execution_time == 1.5
        assert len(result.errors) == 0

    def test_scenario_report(self):
        """Test ScenarioReport model."""
        report = ScenarioReport(
            scenario_name="Test Report",
            success=True,
            turn_results=[],
            total_time=10.5,
            errors=[],
            summary={"total_turns": 5}
        )
        assert report.scenario_name == "Test Report"
        assert report.success is True
        assert report.total_time == 10.5
        assert report.summary["total_turns"] == 5


class TestScenarioRunner:
    """Test ScenarioRunner functionality."""

    def test_runner_initialization(self):
        """Test runner initialization."""
        runner = ScenarioRunner(verbose=True, api_key="test-key")
        assert runner.verbose is True
        assert runner.api_key == "test-key"

    def test_parse_scenario_flat(self):
        """Test parsing flat scenario structure."""
        runner = ScenarioRunner()
        data = {
            "name": "Test",
            "description": "Test scenario",
            "initial_context": {},
            "conversation": [
                {
                    "user": "Hello",
                    "expected": {
                        "agent": "bank_support",
                        "tools_called": ["authenticate_customer"]
                    }
                }
            ]
        }

        scenario = runner._parse_scenario(data)
        assert scenario.name == "Test"
        assert len(scenario.conversation) == 1
        assert scenario.conversation[0].expected_tools == ["authenticate_customer"]

    def test_parse_scenario_nested(self):
        """Test parsing nested scenario structure."""
        runner = ScenarioRunner()
        data = {
            "scenario": {
                "name": "Nested Test",
                "description": "Nested test scenario",
                "initial_context": {},
                "conversation": [
                    {
                        "user_input": "Hello",
                        "expected": {
                            "authenticated": True
                        }
                    }
                ]
            },
            "test_configuration": {
                "max_execution_time_seconds": 30
            }
        }

        scenario = runner._parse_scenario(data)
        assert scenario.name == "Nested Test"
        assert scenario.conversation[0].expected_authentication is True
        assert scenario.metadata["max_execution_time_seconds"] == 30

    def test_validate_turn_success(self):
        """Test successful turn validation."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="Test",
            expected_tools=["tool1"],
            expected_message_contains=["success"],
            expected_authentication=True
        )

        context = create_test_context(authenticated=True)
        result = {
            "response": "Operation was successful",
            "tools_called": ["tool1"],
            "context": context,
            "context_changes": {"field": "value"}
        }

        errors = runner._validate_turn(turn, result)
        assert len(errors) == 0

    def test_validate_turn_failures(self):
        """Test turn validation failures."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="Test",
            expected_tools=["missing_tool"],
            expected_message_contains=["not_in_response"],
            expected_context_updates=["missing_field"],
            expected_authentication=True
        )

        context = create_test_context(authenticated=False)
        result = {
            "response": "Some other response",
            "tools_called": ["different_tool"],
            "context": context,
            "context_changes": {"other_field": "value"}
        }

        errors = runner._validate_turn(turn, result)
        assert len(errors) > 0
        assert any("missing_tool" in e for e in errors)
        assert any("not_in_response" in e for e in errors)
        assert any("missing_field" in e for e in errors)
        assert any("authentication status" in e for e in errors)

    def test_generate_summary(self):
        """Test summary generation."""
        runner = ScenarioRunner()
        scenario = TestScenario(
            name="Test",
            description="Test",
            initial_context={},
            conversation=[]
        )

        context_after = create_test_context(authenticated=True)
        turn_results = [
            TurnResult(
                user_input="Input 1",
                agent_response="Response 1",
                tools_called=["tool1", "tool2"],
                context_before=create_initial_context(),
                context_after=context_after,
                context_changes={},
                execution_time=1.5,
                errors=[]
            ),
            TurnResult(
                user_input="Input 2",
                agent_response="Response 2",
                tools_called=["tool3"],
                context_before=context_after,
                context_after=context_after,
                context_changes={},
                execution_time=2.0,
                errors=["Error 1"]
            )
        ]

        summary = runner._generate_summary(scenario, turn_results)
        assert summary["total_turns"] == 2
        assert summary["total_tools_called"] == 3
        assert summary["total_errors"] == 1
        assert summary["successful_turns"] == 1
        assert summary["failed_turns"] == 1
        assert summary["final_authenticated"] is True
        assert summary["average_turn_time"] == 1.75


@pytest.mark.asyncio
class TestScenarioExecution:
    """Test scenario execution."""

    async def test_run_scenario_file_not_found(self):
        """Test running scenario with non-existent file."""
        runner = ScenarioRunner()

        with pytest.raises(FileNotFoundError):
            await runner.run_scenario("/nonexistent/file.json")

    @patch("src.runner.get_initial_agent")
    async def test_execute_scenario_no_agent(self, mock_get_agent):
        """Test scenario execution with no agent available."""
        mock_get_agent.return_value = None
        runner = ScenarioRunner()

        scenario = TestScenario(
            name="Test",
            description="Test",
            initial_context={},
            conversation=[ConversationTurn(user_input="Hello")]
        )

        report = await runner._execute_scenario(scenario)
        assert report.success is False
        assert "Could not initialize agent" in report.errors

    @patch("src.runner.get_initial_agent")
    async def test_execute_turn(self, mock_get_agent):
        """Test executing a single turn."""
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.run.return_value = Mock(
            data="Test response",
            _tool_calls=[Mock(tool_name="test_tool")]
        )
        mock_get_agent.return_value = mock_agent

        runner = ScenarioRunner()
        context = create_initial_context()
        turn = ConversationTurn(user_input="Test input")

        result = await runner._execute_turn(
            mock_agent,
            context,
            turn,
            turn_number=1
        )

        assert result.user_input == "Test input"
        assert result.agent_response == "Test response"
        assert "test_tool" in result.tools_called
        assert len(result.errors) == 0

    @patch("src.runner.get_initial_agent")
    async def test_execute_turn_with_error(self, mock_get_agent):
        """Test executing turn that raises error."""
        # Mock agent that raises error
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("Test error")
        mock_get_agent.return_value = mock_agent

        runner = ScenarioRunner()
        context = create_initial_context()
        turn = ConversationTurn(user_input="Test input")

        result = await runner._execute_turn(
            mock_agent,
            context,
            turn,
            turn_number=1
        )

        assert "Error: Test error" in result.agent_response
        assert len(result.errors) == 1
        assert "Test error" in result.errors[0]


@pytest.mark.scenario
class TestScenarioFiles:
    """Test with actual scenario files."""

    @pytest.mark.asyncio
    async def test_run_authentication_scenario(self, scenario_files, skip_if_no_api_key, test_database):
        """Test running authentication scenario."""
        runner = ScenarioRunner(verbose=False)
        report = await runner.run_scenario(str(scenario_files["authentication"]))

        assert report.scenario_name == "Authentication Flow"
        assert len(report.turn_results) > 0
        # May fail if API is not available, so just check it ran
        assert report.total_time > 0

    def test_scenario_files_exist(self, scenario_files):
        """Test that scenario files exist."""
        for name, path in scenario_files.items():
            assert path.exists(), f"Scenario file {name} does not exist at {path}"

            # Verify JSON is valid
            with open(path) as f:
                data = json.load(f)
                assert "name" in data or "scenario" in data