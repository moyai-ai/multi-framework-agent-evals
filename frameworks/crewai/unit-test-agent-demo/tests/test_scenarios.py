"""
Integration tests for scenario execution
"""

import pytest
from pathlib import Path
from src.runner import ScenarioRunner
from src.context import TestScenarioDefinition, ConversationTurn


@pytest.mark.scenario
class TestScenarioRunner:
    """Tests for ScenarioRunner class"""

    def test_runner_initialization(self):
        """Test ScenarioRunner initialization"""
        runner = ScenarioRunner(verbose=False)
        assert runner.verbose is False
        assert runner.config is not None

    def test_load_scenario_from_file(self, temp_scenario_file):
        """Test loading scenario from JSON file"""
        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(temp_scenario_file))

        assert isinstance(scenario, TestScenarioDefinition)
        assert scenario.name == "Test Scenario"
        assert len(scenario.conversation) == 1

    def test_load_invalid_scenario_file(self, tmp_path):
        """Test loading invalid scenario file"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json}")

        runner = ScenarioRunner()
        with pytest.raises(ValueError):
            runner.load_scenario(str(invalid_file))

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file"""
        runner = ScenarioRunner()
        with pytest.raises(ValueError):
            runner.load_scenario("/nonexistent/file.json")

    def test_validate_turn_success(self):
        """Test validating a successful turn"""
        runner = ScenarioRunner()

        turn = ConversationTurn(
            user_input="Generate tests",
            expected={
                "message_contains": ["test", "assert"],
                "contains_imports": True,
                "contains_assertions": True,
            },
        )

        crew_output = "import pytest\n\ndef test_example():\n    assert True"

        passed, errors = runner.validate_turn(turn, crew_output)
        assert passed is True
        assert len(errors) == 0

    def test_validate_turn_missing_content(self):
        """Test validation failure for missing content"""
        runner = ScenarioRunner()

        turn = ConversationTurn(
            user_input="Generate tests",
            expected={
                "message_contains": ["test", "assert", "pytest"],
                "contains_imports": True,
                "contains_assertions": True,
            },
        )

        crew_output = "Some incomplete output"

        passed, errors = runner.validate_turn(turn, crew_output)
        assert passed is False
        assert len(errors) > 0

    def test_validate_turn_case_insensitive(self):
        """Test that validation is case-insensitive"""
        runner = ScenarioRunner()

        turn = ConversationTurn(
            user_input="Generate tests", expected={"message_contains": ["TEST", "ASSERT"]}
        )

        crew_output = "import pytest\n\ndef test_example():\n    assert True"

        passed, errors = runner.validate_turn(turn, crew_output)
        assert passed is True

    def test_validate_turn_test_plan_indicators(self):
        """Test validation of test plan creation"""
        runner = ScenarioRunner()

        turn = ConversationTurn(user_input="Plan tests", expected={"test_plan_created": True})

        crew_output = "Test Plan:\n1. Test scenario one\n2. Test scenario two"

        passed, errors = runner.validate_turn(turn, crew_output)
        assert passed is True

    def test_validate_turn_test_code_indicators(self):
        """Test validation of test code generation"""
        runner = ScenarioRunner()

        turn = ConversationTurn(user_input="Generate tests", expected={"test_code_generated": True})

        crew_output = "def test_example():\n    assert True"

        passed, errors = runner.validate_turn(turn, crew_output)
        assert passed is True


@pytest.mark.scenario
class TestScenarioExecution:
    """Tests for scenario execution with mocks"""

    def test_execute_turn_with_mock(self, sample_scenario_data, mock_crew_execution):
        """Test executing a turn with mocked crew"""
        runner = ScenarioRunner(verbose=False)
        scenario = TestScenarioDefinition(**sample_scenario_data)

        result = runner.execute_turn(
            scenario.conversation[0], turn_number=1, context=scenario.initial_context
        )

        assert result.turn_number == 1
        assert result.execution_time > 0

    def test_run_scenario_with_mock(self, temp_scenario_file, mock_crew_execution):
        """Test running full scenario with mocked crew"""
        runner = ScenarioRunner(verbose=False)
        scenario = runner.load_scenario(str(temp_scenario_file))

        report = runner.run_scenario(scenario)

        assert report is not None
        assert len(report.turns) > 0
        assert report.total_execution_time > 0

    def test_save_report(self, tmp_path, sample_scenario_data):
        """Test saving scenario report"""
        from src.context import ScenarioReport, ExecutionResult

        runner = ScenarioRunner()
        scenario = TestScenarioDefinition(**sample_scenario_data)

        turn_result = ExecutionResult(
            turn_number=1,
            user_input="Test",
            crew_output="Output",
            validation_passed=True,
            execution_time=1.0,
        )

        report = ScenarioReport(
            scenario=scenario,
            turns=[turn_result],
            total_execution_time=1.5,
            success=True,
            summary="Test passed",
        )

        output_path = tmp_path / "test_report.json"
        runner.save_report(report, str(output_path))

        assert output_path.exists()

        # Verify content
        import json

        with open(output_path) as f:
            saved_data = json.load(f)

        assert saved_data["success"] is True
        assert saved_data["summary"] == "Test passed"


@pytest.mark.scenario
class TestScenarioLoading:
    """Tests for loading scenarios from directory"""

    def test_load_scenarios_from_directory(self, tmp_path, sample_scenario_data):
        """Test loading multiple scenarios from directory"""
        import json

        # Create multiple scenario files
        for i in range(3):
            scenario_file = tmp_path / f"scenario_{i}.json"
            with open(scenario_file, "w") as f:
                json.dump(sample_scenario_data, f)

        runner = ScenarioRunner()
        scenarios = runner.load_scenarios_from_directory(str(tmp_path))

        assert len(scenarios) == 3

    def test_load_from_empty_directory(self, tmp_path):
        """Test loading from empty directory"""
        runner = ScenarioRunner()
        scenarios = runner.load_scenarios_from_directory(str(tmp_path))

        assert len(scenarios) == 0

    def test_load_from_nonexistent_directory(self):
        """Test loading from nonexistent directory"""
        runner = ScenarioRunner()

        with pytest.raises(ValueError):
            runner.load_scenarios_from_directory("/nonexistent/directory")


@pytest.mark.integration
class TestRealScenarios:
    """Integration tests with real scenario files"""

    def test_load_simple_functions_scenario(self):
        """Test loading the simple functions scenario"""
        scenario_path = Path("src/scenarios/simple_functions.json")

        if not scenario_path.exists():
            pytest.skip("Scenario file not found")

        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(scenario_path))

        assert scenario.name is not None
        assert len(scenario.conversation) > 0
        assert scenario.initial_context.repository_url is not None

    def test_load_class_methods_scenario(self):
        """Test loading the class methods scenario"""
        scenario_path = Path("src/scenarios/class_methods.json")

        if not scenario_path.exists():
            pytest.skip("Scenario file not found")

        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(scenario_path))

        assert scenario.name is not None
        assert "class" in scenario.name.lower() or "method" in scenario.name.lower()

    def test_load_complex_cases_scenario(self):
        """Test loading the complex cases scenario"""
        scenario_path = Path("src/scenarios/complex_cases.json")

        if not scenario_path.exists():
            pytest.skip("Scenario file not found")

        runner = ScenarioRunner()
        scenario = runner.load_scenario(str(scenario_path))

        assert scenario.name is not None
        assert scenario.metadata.get("complexity") == "high"
