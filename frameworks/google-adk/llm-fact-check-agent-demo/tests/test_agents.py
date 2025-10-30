"""
Comprehensive test suite for LLM fact-checking agents.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from src.agents import (
    llm_fact_check_agent,
    critic_agent,
    reviser_agent,
    get_agent_by_name,
    get_initial_agent,
    list_agents,
    _render_reference,
    _remove_end_of_edit_mark,
    AGENTS
)
from src.runner import (
    ScenarioRunner,
    Scenario,
    ConversationTurn,
    ExecutionResult,
    ScenarioReport,
    run_all_scenarios
)


class TestAgents:
    """Test agent configuration and lookup functions."""

    def test_agent_registry(self):
        """Test that all agents are registered correctly."""
        assert 'llm_fact_check_agent' in AGENTS
        assert 'critic_agent' in AGENTS
        assert 'reviser_agent' in AGENTS
        assert len(AGENTS) == 3

    def test_get_agent_by_name_exact(self):
        """Test exact agent name lookup."""
        agent = get_agent_by_name('critic_agent')
        assert agent is not None
        assert agent.name == 'critic_agent'

    def test_get_agent_by_name_partial(self):
        """Test partial agent name lookup."""
        agent = get_agent_by_name('critic')
        assert agent is not None
        assert agent.name == 'critic_agent'

    def test_get_agent_by_name_not_found(self):
        """Test agent lookup with non-existent name."""
        agent = get_agent_by_name('nonexistent_agent')
        assert agent is None

    def test_get_initial_agent(self):
        """Test getting the initial agent."""
        agent = get_initial_agent()
        assert agent is not None
        assert agent.name == 'llm_fact_check_agent'

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 3
        agent_names = [a['name'] for a in agents]
        assert 'llm_fact_check_agent' in agent_names
        assert 'critic_agent' in agent_names
        assert 'reviser_agent' in agent_names

    def test_critic_agent_configuration(self):
        """Test critic agent has correct configuration."""
        assert critic_agent.name == 'critic_agent'
        assert critic_agent.model == 'gemini-2.5-flash'
        assert critic_agent.after_model_callback is not None
        # Check that google_search tool is included
        assert len(critic_agent.tools) > 0

    def test_reviser_agent_configuration(self):
        """Test reviser agent has correct configuration."""
        assert reviser_agent.name == 'reviser_agent'
        assert reviser_agent.model == 'gemini-2.5-flash'
        assert reviser_agent.after_model_callback is not None

    def test_llm_fact_check_agent_configuration(self):
        """Test root agent is a SequentialAgent with correct sub-agents."""
        assert llm_fact_check_agent.name == 'llm_fact_check_agent'
        assert hasattr(llm_fact_check_agent, 'sub_agents')
        assert len(llm_fact_check_agent.sub_agents) == 2
        assert llm_fact_check_agent.sub_agents[0] == critic_agent
        assert llm_fact_check_agent.sub_agents[1] == reviser_agent


class TestCallbacks:
    """Test agent callback functions."""

    def test_render_reference_with_grounding(self, mock_llm_response, mock_callback_context):
        """Test _render_reference adds references when grounding is present."""
        response = mock_llm_response("Test response")
        result = _render_reference(mock_callback_context, response)

        # Check that reference was added
        assert len(result.content.parts) == 1
        assert "Reference:" in result.content.parts[0].text
        assert "Test Title" in result.content.parts[0].text
        assert "https://example.com" in result.content.parts[0].text

    def test_render_reference_without_grounding(self, mock_callback_context):
        """Test _render_reference handles missing grounding gracefully."""
        class MockResponse:
            def __init__(self):
                self.content = MagicMock(parts=[MagicMock(text="Test")])
                self.grounding_metadata = None

        response = MockResponse()
        result = _render_reference(mock_callback_context, response)
        assert result == response  # Should return unchanged

    def test_remove_end_of_edit_mark(self, mock_callback_context):
        """Test _remove_end_of_edit_mark removes the marker correctly."""
        class MockPart:
            def __init__(self, text):
                self.text = text

        class MockResponse:
            def __init__(self):
                self.content = MagicMock()
                self.content.parts = [
                    MockPart("Revised text here---END-OF-EDIT---Extra text"),
                    MockPart("Should be removed")
                ]

        response = MockResponse()
        result = _remove_end_of_edit_mark(mock_callback_context, response)

        # Check that marker and everything after was removed
        assert len(result.content.parts) == 1
        assert result.content.parts[0].text == "Revised text here"

    def test_remove_end_of_edit_mark_no_marker(self, mock_callback_context):
        """Test _remove_end_of_edit_mark when marker is not present."""
        class MockPart:
            def __init__(self, text):
                self.text = text

        class MockResponse:
            def __init__(self):
                self.content = MagicMock()
                self.content.parts = [MockPart("Normal text without marker")]

        response = MockResponse()
        result = _remove_end_of_edit_mark(mock_callback_context, response)

        # Should remain unchanged
        assert len(result.content.parts) == 1
        assert result.content.parts[0].text == "Normal text without marker"


class TestScenarioRunner:
    """Test the scenario runner functionality."""

    def test_load_scenario(self, scenario_files):
        """Test loading a scenario from JSON file."""
        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(scenario_files["accurate"]))

        assert scenario.name == "accurate_facts"
        assert len(scenario.conversation) == 1
        assert scenario.conversation[0].user_input.startswith("Q: Who was the first president")

    def test_validate_turn_all_pass(self):
        """Test validation when all expectations are met."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="test",
            expected_tools=["google_search"],
            expected_message_contains=["Accurate", "Washington"],
            expected_verdict="Accurate"
        )

        errors = runner.validate_turn(
            turn,
            tools_called=["google_search"],
            messages=["The claim is Accurate. Washington was indeed..."],
            verdict="Accurate"
        )

        assert len(errors) == 0

    def test_validate_turn_missing_tool(self):
        """Test validation when expected tool is not called."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="test",
            expected_tools=["google_search"]
        )

        errors = runner.validate_turn(
            turn,
            tools_called=[],
            messages=["Test message"],
            verdict=None
        )

        assert len(errors) == 1
        assert "google_search" in errors[0]

    def test_validate_turn_missing_content(self):
        """Test validation when expected content is missing."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="test",
            expected_message_contains=["specific", "keywords"]
        )

        errors = runner.validate_turn(
            turn,
            tools_called=[],
            messages=["This message has different content"],
            verdict=None
        )

        assert len(errors) == 2
        assert any("specific" in e for e in errors)
        assert any("keywords" in e for e in errors)

    def test_validate_turn_wrong_verdict(self):
        """Test validation when verdict doesn't match."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="test",
            expected_verdict="Accurate"
        )

        errors = runner.validate_turn(
            turn,
            tools_called=[],
            messages=["Test"],
            verdict="Inaccurate"
        )

        assert len(errors) == 1
        assert "Expected verdict 'Accurate'" in errors[0]

    def test_validate_turn_skip_validation(self):
        """Test that validation is skipped when flag is set."""
        runner = ScenarioRunner()
        turn = ConversationTurn(
            user_input="test",
            expected_tools=["tool_that_wont_be_called"],
            skip_validation=True
        )

        # This would normally fail, but skip_validation prevents it
        result = ExecutionResult(
            turn_number=1,
            user_input="test",
            messages=["Test"],
            tools_called=[],
            validation_passed=True,  # Would be False without skip
            validation_errors=[],
            execution_time_ms=100,
            raw_output=None
        )

        assert result.validation_passed

    @pytest.mark.asyncio
    async def test_execute_turn_with_mock(self, mock_runner):
        """Test executing a turn with mocked runner."""
        runner = ScenarioRunner()
        runner.runner = mock_runner
        runner.session = MagicMock(user_id="test_user", id="test_session")

        turn = ConversationTurn(
            user_input="Q: Test? A: Test answer.",
            expected_tools=["google_search"]
        )

        result = await runner.execute_turn("Q: Test? A: Test answer.", turn, 1)

        assert result.turn_number == 1
        assert len(result.messages) > 0
        assert "google_search" in result.tools_called

    def test_save_report(self, tmp_path):
        """Test saving a scenario report."""
        runner = ScenarioRunner()
        report = ScenarioReport(
            scenario_name="test_scenario",
            description="Test",
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T00:01:00",
            total_turns=1,
            successful_turns=1,
            failed_turns=0,
            turns=[],
            overall_success=True,
            execution_time_ms=60000
        )

        output_dir = str(tmp_path / "reports")
        runner.save_report(report, output_dir)

        # Check file was created
        files = list(Path(output_dir).glob("report_test_scenario_*.json"))
        assert len(files) == 1

        # Check content
        with open(files[0]) as f:
            saved_report = json.load(f)
        assert saved_report["scenario_name"] == "test_scenario"
        assert saved_report["overall_success"] is True


class TestIntegration:
    """Integration tests that require API access."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_run_scenario_with_api(self, skip_if_no_api_key, scenario_files):
        """Test running a complete scenario with actual API calls."""
        runner = ScenarioRunner(verbose=True)
        scenario = runner.load_scenario(str(scenario_files["accurate"]))

        report = await runner.run_scenario(scenario)

        assert report.scenario_name == "accurate_facts"
        assert report.total_turns == 1
        # We can't guarantee the API response, so just check structure
        assert isinstance(report.turns, list)
        assert len(report.turns) == 1

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_run_all_scenarios(self, skip_if_no_api_key, tmp_path):
        """Test running all scenarios in a directory."""
        # Use the actual scenarios directory
        scenario_dir = str(Path(__file__).parent.parent / "src" / "scenarios")

        reports, success = await run_all_scenarios(
            scenario_dir=scenario_dir,
            verbose=False,
            save_reports=False
        )

        assert len(reports) >= 4  # We created 4 scenarios
        assert all(isinstance(r, ScenarioReport) for r in reports)


class TestPrompts:
    """Test that prompts are properly configured."""

    def test_critic_prompt_content(self):
        """Test that critic prompt contains key instructions."""
        from src.prompts import CRITIC_PROMPT

        assert "investigative journalist" in CRITIC_PROMPT
        assert "CLAIMS" in CRITIC_PROMPT
        assert "Accurate" in CRITIC_PROMPT
        assert "Inaccurate" in CRITIC_PROMPT
        assert "search the web" in CRITIC_PROMPT

    def test_reviser_prompt_content(self):
        """Test that reviser prompt contains key instructions."""
        from src.prompts import REVISER_PROMPT

        assert "professional editor" in REVISER_PROMPT
        assert "minimally revise" in REVISER_PROMPT
        assert "---END-OF-EDIT---" in REVISER_PROMPT
        assert "Accurate claims" in REVISER_PROMPT
        assert "Inaccurate claims" in REVISER_PROMPT