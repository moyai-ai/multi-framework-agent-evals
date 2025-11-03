"""
Unit tests for CrewAI crew configuration
"""

import pytest
from src.crew import create_unit_test_crew, run_unit_test_generation
from crewai import Crew


@pytest.mark.unit
class TestCrewCreation:
    """Tests for crew creation"""

    def test_create_unit_test_crew(self):
        """Test creating a unit test crew"""
        crew = create_unit_test_crew("https://github.com/test/repo")

        assert isinstance(crew, Crew)
        assert len(crew.agents) == 3
        assert len(crew.tasks) == 3

    def test_create_crew_with_file_path(self):
        """Test creating crew with specific file path"""
        crew = create_unit_test_crew("https://github.com/test/repo", file_path="test.py")

        assert isinstance(crew, Crew)
        # Check that file path is in first task description
        assert "test.py" in crew.tasks[0].description

    def test_create_crew_with_function_name(self):
        """Test creating crew with specific function name"""
        crew = create_unit_test_crew("https://github.com/test/repo", function_name="test_func")

        assert isinstance(crew, Crew)
        # Check that function name is in first task description
        assert "test_func" in crew.tasks[0].description

    def test_create_crew_with_verbose(self):
        """Test creating crew with verbose mode"""
        crew = create_unit_test_crew("https://github.com/test/repo", verbose=True)

        assert crew.verbose is True

    def test_create_crew_without_verbose(self):
        """Test creating crew without verbose mode"""
        crew = create_unit_test_crew("https://github.com/test/repo", verbose=False)

        assert crew.verbose is False


@pytest.mark.unit
class TestCrewConfiguration:
    """Tests for crew configuration"""

    def test_crew_has_sequential_process(self):
        """Test that crew uses sequential process"""
        from crewai import Process

        crew = create_unit_test_crew("https://github.com/test/repo")
        assert crew.process == Process.sequential

    def test_crew_agents_order(self):
        """Test that agents are in correct order"""
        crew = create_unit_test_crew("https://github.com/test/repo")

        agent_roles = [agent.role for agent in crew.agents]
        assert agent_roles[0] == "Code Analyzer"
        assert agent_roles[1] == "Test Planner"
        assert agent_roles[2] == "Test Writer"

    def test_crew_tasks_order(self):
        """Test that tasks are in correct order"""
        crew = create_unit_test_crew("https://github.com/test/repo")

        # Check that tasks target the right agents
        assert crew.tasks[0].agent.role == "Code Analyzer"
        assert crew.tasks[1].agent.role == "Test Planner"
        assert crew.tasks[2].agent.role == "Test Writer"

    def test_crew_task_dependencies(self):
        """Test that tasks have proper context dependencies"""
        crew = create_unit_test_crew("https://github.com/test/repo")

        # Planning task depends on analysis task
        assert crew.tasks[0] in crew.tasks[1].context

        # Generation task depends on planning task
        assert crew.tasks[1] in crew.tasks[2].context


@pytest.mark.unit
class TestRunUnitTestGeneration:
    """Tests for run_unit_test_generation convenience function"""

    def test_run_unit_test_generation_returns_dict(self, mock_crew_execution):
        """Test that run function returns a dict"""
        result = run_unit_test_generation("https://github.com/test/repo")

        assert isinstance(result, dict)
        assert "repository_url" in result
        assert "result" in result

    def test_run_with_file_path(self, mock_crew_execution):
        """Test run with file path"""
        result = run_unit_test_generation("https://github.com/test/repo", file_path="test.py")

        assert result["file_path"] == "test.py"

    def test_run_with_function_name(self, mock_crew_execution):
        """Test run with function name"""
        result = run_unit_test_generation(
            "https://github.com/test/repo", function_name="test_func"
        )

        assert result["function_name"] == "test_func"

    def test_run_includes_raw_output(self, mock_crew_execution):
        """Test that result includes raw output"""
        result = run_unit_test_generation("https://github.com/test/repo")

        assert "raw_output" in result
        assert isinstance(result["raw_output"], str)
