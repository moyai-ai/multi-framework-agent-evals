"""
Unit tests for context models and configuration
"""

import pytest
from src.context import (
    Config,
    FunctionInfo,
    TestScenario,
    TestPlan,
    GeneratedTest,
    AnalysisRequest,
    AnalysisResult,
    ScenarioExpectation,
    ConversationTurn,
    TestScenarioDefinition,
    ExecutionResult,
    ScenarioReport,
)


@pytest.mark.unit
class TestConfig:
    """Tests for Config class"""

    def test_config_initialization(self):
        """Test that config initializes with defaults"""
        config = Config()
        assert config.OPENAI_MODEL_NAME == "gpt-4o"
        assert config.MAX_ITERATIONS == 10
        assert config.VERBOSE is False  # Set by test fixture
        assert config.RUN_FULL_SCENARIOS is False


@pytest.mark.unit
class TestFunctionInfo:
    """Tests for FunctionInfo model"""

    def test_function_info_creation(self, sample_function_info):
        """Test creating FunctionInfo from dict"""
        func_info = FunctionInfo(**sample_function_info)
        assert func_info.name == "calculate_discount"
        assert func_info.return_type == "float"
        assert len(func_info.parameters) == 2
        assert func_info.is_async is False

    def test_function_info_with_class(self):
        """Test FunctionInfo for class method"""
        data = {
            "name": "add_item",
            "module": "shopping",
            "line_number": 10,
            "source_code": "def add_item(self, item): pass",
            "class_name": "ShoppingCart",
        }
        func_info = FunctionInfo(**data)
        assert func_info.class_name == "ShoppingCart"

    def test_function_info_async_function(self):
        """Test FunctionInfo for async function"""
        data = {
            "name": "async_fetch",
            "module": "api",
            "line_number": 5,
            "source_code": "async def async_fetch(): pass",
            "is_async": True,
        }
        func_info = FunctionInfo(**data)
        assert func_info.is_async is True


@pytest.mark.unit
class TestTestScenario:
    """Tests for TestScenario model"""

    def test_test_scenario_creation(self):
        """Test creating TestScenario"""
        scenario = TestScenario(
            name="valid_input",
            description="Test with valid inputs",
            inputs={"x": 1, "y": 2},
            expected_output=3,
        )
        assert scenario.name == "valid_input"
        assert scenario.inputs["x"] == 1
        assert scenario.expected_exception is None

    def test_test_scenario_with_exception(self):
        """Test TestScenario expecting exception"""
        scenario = TestScenario(
            name="invalid_input",
            description="Test with invalid input",
            inputs={"x": -1},
            expected_output=None,
            expected_exception="ValueError",
        )
        assert scenario.expected_exception == "ValueError"


@pytest.mark.unit
class TestTestPlan:
    """Tests for TestPlan model"""

    def test_test_plan_creation(self, sample_test_plan):
        """Test creating TestPlan"""
        plan = TestPlan(**sample_test_plan)
        assert plan.function_name == "calculate_discount"
        assert len(plan.scenarios) == 3
        assert plan.test_class_name == "TestCalculateDiscount"

    def test_test_plan_with_mocks(self):
        """Test TestPlan with mocking requirements"""
        plan = TestPlan(
            function_name="api_call",
            module_path="api",
            test_class_name="TestApiCall",
            scenarios=[],
            mocks_needed=[{"target": "requests.get", "return_value": "mock_response"}],
        )
        assert len(plan.mocks_needed) == 1


@pytest.mark.unit
class TestAnalysisRequest:
    """Tests for AnalysisRequest model"""

    def test_analysis_request_creation(self):
        """Test creating AnalysisRequest"""
        request = AnalysisRequest(
            repository_url="https://github.com/test/repo", file_path="test.py"
        )
        assert request.repository_url == "https://github.com/test/repo"
        assert request.branch == "main"  # default
        assert request.analysis_type == "all"  # default

    def test_analysis_request_custom_branch(self):
        """Test AnalysisRequest with custom branch"""
        request = AnalysisRequest(
            repository_url="https://github.com/test/repo", branch="develop"
        )
        assert request.branch == "develop"


@pytest.mark.unit
class TestScenarioExpectation:
    """Tests for ScenarioExpectation model"""

    def test_scenario_expectation_defaults(self):
        """Test ScenarioExpectation default values"""
        expectation = ScenarioExpectation()
        assert expectation.functions_found_min == 1
        assert expectation.test_plan_created is True
        assert expectation.test_code_generated is True
        assert expectation.test_scenarios_min == 1

    def test_scenario_expectation_custom(self):
        """Test ScenarioExpectation with custom values"""
        expectation = ScenarioExpectation(
            functions_found_min=3, message_contains=["test", "assert"]
        )
        assert expectation.functions_found_min == 3
        assert len(expectation.message_contains) == 2


@pytest.mark.unit
class TestTestScenarioDefinition:
    """Tests for TestScenarioDefinition model"""

    def test_scenario_definition_creation(self, sample_scenario_data):
        """Test creating TestScenarioDefinition"""
        scenario = TestScenarioDefinition(**sample_scenario_data)
        assert scenario.name == "Test Scenario"
        assert len(scenario.conversation) == 1
        assert scenario.metadata["test_type"] == "unit"

    def test_scenario_definition_initial_context(self, sample_scenario_data):
        """Test that initial_context is properly parsed"""
        scenario = TestScenarioDefinition(**sample_scenario_data)
        assert isinstance(scenario.initial_context, AnalysisRequest)
        assert scenario.initial_context.repository_url == "https://github.com/test/repo"


@pytest.mark.unit
class TestExecutionResult:
    """Tests for ExecutionResult model"""

    def test_execution_result_success(self):
        """Test successful ExecutionResult"""
        result = ExecutionResult(
            turn_number=1,
            user_input="Test input",
            crew_output="Test output with def test_ and assert",
            validation_passed=True,
            execution_time=1.5,
        )
        assert result.validation_passed is True
        assert result.execution_time == 1.5
        assert len(result.validation_errors) == 0

    def test_execution_result_failure(self):
        """Test failed ExecutionResult"""
        result = ExecutionResult(
            turn_number=1,
            user_input="Test input",
            crew_output="Incomplete output",
            validation_passed=False,
            validation_errors=["Missing test code", "Missing assertions"],
            execution_time=0.5,
        )
        assert result.validation_passed is False
        assert len(result.validation_errors) == 2


@pytest.mark.unit
class TestScenarioReport:
    """Tests for ScenarioReport model"""

    def test_scenario_report_creation(self, sample_scenario_data):
        """Test creating ScenarioReport"""
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

        assert report.success is True
        assert len(report.turns) == 1
        assert report.total_execution_time == 1.5
