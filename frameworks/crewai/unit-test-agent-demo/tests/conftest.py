"""
Pytest configuration and fixtures
"""

import os
import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-4o")
    monkeypatch.setenv("VERBOSE", "false")
    monkeypatch.setenv("RUN_FULL_SCENARIOS", "false")


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing"""
    return '''
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate the discounted price.

    Args:
        price: Original price
        discount_percent: Discount percentage (0-100)

    Returns:
        Discounted price

    Raises:
        ValueError: If discount_percent is not between 0 and 100
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("Discount must be between 0 and 100")

    return price * (1 - discount_percent / 100)


class ShoppingCart:
    """Simple shopping cart class"""

    def __init__(self):
        self.items = []

    def add_item(self, item: str, price: float) -> None:
        """Add an item to the cart"""
        self.items.append({"item": item, "price": price})

    def get_total(self) -> float:
        """Calculate total price of all items"""
        return sum(item["price"] for item in self.items)
'''


@pytest.fixture
def sample_function_info():
    """Sample function information from AST parsing"""
    return {
        "name": "calculate_discount",
        "module": "test_module",
        "line_number": 2,
        "parameters": [
            {"name": "price", "type": "float", "default": None},
            {"name": "discount_percent", "type": "float", "default": None},
        ],
        "return_type": "float",
        "docstring": "Calculate the discounted price.",
        "source_code": "def calculate_discount(price: float, discount_percent: float) -> float: ...",
        "is_async": False,
        "decorators": [],
        "class_name": None,
    }


@pytest.fixture
def sample_test_plan():
    """Sample test plan"""
    return {
        "function_name": "calculate_discount",
        "module_path": "test_module",
        "test_class_name": "TestCalculateDiscount",
        "scenarios": [
            {
                "name": "valid_discount",
                "description": "Test with valid discount percentage",
                "inputs": {"price": 100.0, "discount_percent": 20.0},
                "expected_output": 80.0,
                "expected_exception": None,
            },
            {
                "name": "zero_discount",
                "description": "Test with zero discount",
                "inputs": {"price": 100.0, "discount_percent": 0.0},
                "expected_output": 100.0,
                "expected_exception": None,
            },
            {
                "name": "invalid_discount",
                "description": "Test with invalid discount percentage",
                "inputs": {"price": 100.0, "discount_percent": 150.0},
                "expected_output": None,
                "expected_exception": "ValueError",
            },
        ],
        "fixtures_needed": [],
        "imports_needed": ["pytest"],
        "mocks_needed": [],
    }


@pytest.fixture
def sample_generated_test_code():
    """Sample generated test code"""
    return '''
import pytest
from test_module import calculate_discount


class TestCalculateDiscount:
    """Tests for calculate_discount function"""

    def test_valid_discount(self):
        """Test with valid discount percentage"""
        result = calculate_discount(100.0, 20.0)
        assert result == 80.0

    def test_zero_discount(self):
        """Test with zero discount"""
        result = calculate_discount(100.0, 0.0)
        assert result == 100.0

    def test_invalid_discount(self):
        """Test with invalid discount percentage"""
        with pytest.raises(ValueError):
            calculate_discount(100.0, 150.0)
'''


@pytest.fixture
def mock_git_repo(monkeypatch):
    """Mock git.Repo for testing"""
    mock_repo = MagicMock()
    mock_clone = MagicMock(return_value=mock_repo)

    def mock_clone_from(url, path, **kwargs):
        # Create a fake Python file in the temp directory
        temp_path = Path(path)
        temp_path.mkdir(parents=True, exist_ok=True)
        test_file = temp_path / "test.py"
        test_file.write_text("def test_function(): pass")
        return mock_repo

    monkeypatch.setattr("git.Repo.clone_from", mock_clone_from)
    return mock_repo


@pytest.fixture
def mock_crew_execution(monkeypatch):
    """Mock CrewAI crew execution"""
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: "Test execution completed successfully"

    def mock_kickoff(self):
        return mock_result

    monkeypatch.setattr("crewai.Crew.kickoff", mock_kickoff)
    return mock_result


@pytest.fixture
def sample_scenario_data():
    """Sample scenario data for testing"""
    return {
        "name": "Test Scenario",
        "description": "A test scenario",
        "initial_context": {
            "repository_url": "https://github.com/test/repo",
            "file_path": "test.py",
            "function_name": "test_function",
            "branch": "main",
            "analysis_type": "single_function",
        },
        "conversation": [
            {
                "user_input": "Generate tests for test_function",
                "expected": {
                    "functions_found_min": 1,
                    "test_plan_created": True,
                    "test_code_generated": True,
                    "test_scenarios_min": 2,
                    "contains_imports": True,
                    "contains_assertions": True,
                    "message_contains": ["test", "def test_"],
                },
            }
        ],
        "metadata": {"test_type": "unit", "priority": "high"},
    }


@pytest.fixture
def temp_scenario_file(tmp_path, sample_scenario_data):
    """Create a temporary scenario file"""
    import json

    scenario_file = tmp_path / "test_scenario.json"
    with open(scenario_file, "w") as f:
        json.dump(sample_scenario_data, f)
    return scenario_file


@pytest.fixture
def skip_if_no_api_key():
    """Skip test if no OpenAI API key is available"""
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test-api-key":
        pytest.skip("OpenAI API key not available")
