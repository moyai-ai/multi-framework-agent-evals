"""
Tests for scenario execution and validation.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.runner import ScenarioRunner, Scenario, ConversationTurn
from src.context import Config

pytestmark = pytest.mark.scenario


class TestScenarioLoading:
    """Test scenario loading functionality."""

    def test_load_scenarios(self, scenario_runner, tmp_path):
        """Test loading scenarios from directory."""
        # Create temporary scenarios directory
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        scenario_runner.scenarios_dir = scenarios_dir

        # Create a test scenario file
        scenario_data = {
            "name": "Test Scenario",
            "description": "Test description",
            "initial_context": {"repository_url": "https://github.com/test/repo"},
            "conversation": [
                {
                    "user": "Test input",
                    "expected": {"message_contains": ["test"]}
                }
            ],
            "metadata": {"test": True}
        }
        (scenarios_dir / "test_scenario.json").write_text(json.dumps(scenario_data))

        scenarios = scenario_runner.load_scenarios()

        assert isinstance(scenarios, list)
        assert len(scenarios) == 1
        assert scenarios[0].name == "Test Scenario"

    def test_scenario_structure(self, test_scenario):
        """Test scenario data structure."""
        assert test_scenario.name == "Test Security Analysis"
        assert test_scenario.description == "Test scenario for security analysis"
        assert test_scenario.initial_context["repository_url"] == "https://github.com/test/repo"
        assert len(test_scenario.conversation) == 1
        assert test_scenario.conversation[0].user == "Analyze the security of this repository"


class TestScenarioExecution:
    """Test scenario execution."""

    @pytest.mark.asyncio
    async def test_run_scenario(self, scenario_runner, test_scenario):
        """Test running a single scenario."""
        with patch("src.manager.AnalysisManager.analyze_repository") as mock_analyze:
            mock_analyze.return_value = {
                "final_report": "Test analysis complete",
                "issues_found": [{"rule_id": "test-issue"}],
                "files_analyzed": ["test.py"]
            }

            result = await scenario_runner.run_scenario(test_scenario)

            assert result["name"] == "Test Security Analysis"
            assert result["success"] is True
            assert result["files_analyzed"] == 1
            assert result["issues_found"] == 1

    @pytest.mark.asyncio
    async def test_run_scenario_with_error(self, scenario_runner, test_scenario):
        """Test scenario execution with error handling."""
        with patch("src.manager.AnalysisManager.analyze_repository") as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")

            result = await scenario_runner.run_scenario(test_scenario)

            assert result["success"] is False
            assert "error" in result
            assert "Test error" in str(result["error"])

    @pytest.mark.asyncio
    async def test_run_all_scenarios(self, scenario_runner, tmp_path):
        """Test running all scenarios."""
        # Create a temporary directory with scenario files
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()

        # Create test scenario files
        scenario1 = {
            "name": "Scenario 1",
            "description": "Test 1",
            "initial_context": {"repository_url": "https://github.com/test/repo1"},
            "conversation": [{"user": "Test 1", "expected": {"message_contains": ["test"]}}]
        }
        (scenarios_dir / "scenario1.json").write_text(json.dumps(scenario1))

        # Patch both run_agent and the manager's analyze_repository to prevent actual execution
        with patch("src.manager.AnalysisManager.analyze_repository") as mock_analyze:
            mock_analyze.return_value = {
                "repository": "test/repo1",
                "analysis_type": "security",
                "final_report": "Analysis complete",
                "issues_found": [],
                "files_analyzed": [],
                "steps_taken": 0,
                "error": None
            }

            results = await scenario_runner.run_all_scenarios(str(scenarios_dir))

            assert isinstance(results, list)
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_run_specific_scenario(self, scenario_runner):
        """Test running a specific scenario by name."""
        with patch.object(scenario_runner, "load_scenarios") as mock_load:
            test_scenario = Scenario(
                name="Target Scenario",
                description="Specific test",
                initial_context={"repository_url": "https://github.com/test/specific"},
                conversation=[ConversationTurn("Test", {"message_contains": ["test"]})]
            )
            mock_load.return_value = [
                test_scenario,
                Scenario(
                    name="Other Scenario",
                    description="Other test",
                    initial_context={"repository_url": "https://github.com/test/other"},
                    conversation=[ConversationTurn("Other", {"message_contains": ["other"]})]
                )
            ]

            with patch.object(scenario_runner, "run_scenario") as mock_run:
                mock_run.return_value = {"name": "Target Scenario", "success": True}

                result = await scenario_runner.run_specific_scenario("Target Scenario")

                assert result["name"] == "Target Scenario"
                mock_run.assert_called_once_with(test_scenario)


class TestExpectationValidation:
    """Test expectation validation logic."""

    def test_validate_expectations_actions(self, scenario_runner):
        """Test validating expected actions."""
        turn = ConversationTurn(
            user="Test",
            expected={"actions": ["fetch_repository_info", "analyze_files"]}
        )
        turn.actions_taken = ["fetch_repository_info", "analyze_files", "generate_report"]

        response = {"issues_found": [], "final_report": "Test"}
        result = scenario_runner._validate_expectations(turn, response)

        assert result is True

    def test_validate_expectations_findings(self, scenario_runner):
        """Test validating expected findings."""
        turn = ConversationTurn(
            user="Test",
            expected={"findings": ["sql-injection", "xss-vulnerability"]}
        )
        turn.findings = [
            {"rule_id": "sql-injection"},
            {"rule_id": "xss-vulnerability"},
            {"rule_id": "hardcoded-secret"}
        ]

        response = {"issues_found": turn.findings, "final_report": "Test"}
        result = scenario_runner._validate_expectations(turn, response)

        assert result is True

    def test_validate_expectations_message_contains(self, scenario_runner):
        """Test validating message content."""
        turn = ConversationTurn(
            user="Test",
            expected={"message_contains": ["security", "vulnerability"]}
        )
        turn.actual_response = "Security analysis found vulnerability issues"

        response = {"final_report": turn.actual_response}
        result = scenario_runner._validate_expectations(turn, response)

        assert result is True

    def test_validate_expectations_severity(self, scenario_runner):
        """Test validating severity levels."""
        turn = ConversationTurn(
            user="Test",
            expected={"severity_contains": ["HIGH", "CRITICAL"]}
        )
        turn.findings = [
            {"severity": "HIGH"},
            {"severity": "CRITICAL"},
            {"severity": "MEDIUM"}
        ]

        response = {"issues_found": turn.findings}
        result = scenario_runner._validate_expectations(turn, response)

        assert result is True

    def test_validate_expectations_failure(self, scenario_runner):
        """Test validation failure."""
        turn = ConversationTurn(
            user="Test",
            expected={"message_contains": ["missing_keyword"]}
        )
        turn.actual_response = "This response does not contain the expected keyword"

        response = {"final_report": turn.actual_response}
        result = scenario_runner._validate_expectations(turn, response)

        assert result is False


class TestResultsHandling:
    """Test results handling and reporting."""

    def test_calculate_metrics(self, scenario_runner, test_scenario):
        """Test metrics calculation."""
        results = {
            "turns": [
                {"success": True, "findings_count": 3, "actions": ["a1", "a2"]},
                {"success": True, "findings_count": 2, "actions": ["a3"]},
                {"success": False, "findings_count": 1, "actions": ["a4", "a5"]}
            ]
        }

        metrics = scenario_runner._calculate_metrics(test_scenario, results)

        assert abs(metrics["success_rate"] - 0.6667) < 0.01  # 2/3 successful
        assert metrics["total_findings"] == 6  # 3+2+1
        assert metrics["total_actions"] == 5  # 2+1+2

    def test_generate_summary(self, scenario_runner):
        """Test summary generation."""
        all_results = [
            {"success": True, "execution_time": 10},
            {"success": False, "execution_time": 15},
            {"success": True, "execution_time": 12}
        ]

        summary = scenario_runner._generate_summary(all_results)

        assert summary["total_scenarios"] == 3
        assert summary["successful_scenarios"] == 2
        assert summary["failed_scenarios"] == 1
        assert abs(summary["success_rate"] - 0.6667) < 0.01
        assert summary["total_execution_time"] == 37
        assert abs(summary["average_execution_time"] - 12.33) < 0.01

    def test_save_results(self, scenario_runner, tmp_path):
        """Test saving results to file."""
        # Add results to scenario_runner.results
        scenario_runner.results = [
            {"test": "results", "success": True},
            {"test": "results2", "success": False}
        ]
        output_file = tmp_path / "test_output.json"

        scenario_runner.save_results(str(output_file))

        assert output_file.exists()
        with open(output_file) as f:
            saved = json.load(f)
        assert "results" in saved
        assert "total_scenarios" in saved
        assert saved["total_scenarios"] == 2

    def test_print_summary(self, scenario_runner, capsys):
        """Test printing summary to console."""
        # Add results to scenario_runner.results
        scenario_runner.results = [
            {
                "scenario_name": "Test Scenario",
                "success": True,
                "execution_time": 10.5,
                "files_analyzed": 3,
                "issues_found": 5
            },
            {
                "scenario_name": "Test Scenario 2",
                "success": False,
                "execution_time": 8.0,
                "files_analyzed": 2,
                "issues_found": 0
            }
        ]

        scenario_runner.print_summary()
        captured = capsys.readouterr()

        assert "SCENARIO EXECUTION SUMMARY" in captured.out
        assert "Total Scenarios: 2" in captured.out