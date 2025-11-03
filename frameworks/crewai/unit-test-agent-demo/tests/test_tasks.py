"""
Unit tests for CrewAI tasks
"""

import pytest
from src.tasks import (
    create_analysis_task,
    create_planning_task,
    create_test_generation_task,
    create_sequential_tasks,
)


@pytest.mark.unit
class TestTaskCreation:
    """Tests for task creation functions"""

    def test_create_analysis_task(self):
        """Test creating an analysis task"""
        task = create_analysis_task("https://github.com/test/repo")
        assert task is not None
        assert "repository" in task.description.lower()
        assert task.agent is not None

    def test_create_analysis_task_with_file_path(self):
        """Test creating analysis task with specific file"""
        task = create_analysis_task("https://github.com/test/repo", file_path="src/main.py")
        assert "src/main.py" in task.description

    def test_create_analysis_task_with_function_name(self):
        """Test creating analysis task with specific function"""
        task = create_analysis_task(
            "https://github.com/test/repo", function_name="calculate_discount"
        )
        assert "calculate_discount" in task.description

    def test_create_planning_task(self):
        """Test creating a planning task"""
        task = create_planning_task()
        assert task is not None
        assert "test plan" in task.description.lower()
        assert task.agent is not None

    def test_create_planning_task_with_context(self):
        """Test creating planning task with analysis context"""
        context = "Function: calculate_discount"
        task = create_planning_task(analysis_context=context)
        assert context in task.description

    def test_create_test_generation_task(self):
        """Test creating a test generation task"""
        task = create_test_generation_task()
        assert task is not None
        assert "pytest" in task.description.lower()
        assert task.agent is not None

    def test_create_test_generation_task_with_context(self):
        """Test creating generation task with plan context"""
        context = "Test Plan: 5 scenarios"
        task = create_test_generation_task(plan_context=context)
        assert context in task.description


@pytest.mark.unit
class TestTaskConfiguration:
    """Tests for task configuration"""

    def test_tasks_have_descriptions(self):
        """Test that all tasks have descriptions"""
        tasks = create_sequential_tasks("https://github.com/test/repo")
        for task in tasks:
            assert task.description is not None
            assert len(task.description) > 0

    def test_tasks_have_expected_output(self):
        """Test that all tasks have expected output defined"""
        tasks = create_sequential_tasks("https://github.com/test/repo")
        for task in tasks:
            assert task.expected_output is not None
            assert len(task.expected_output) > 0

    def test_tasks_have_agents(self):
        """Test that all tasks have agents assigned"""
        tasks = create_sequential_tasks("https://github.com/test/repo")
        for task in tasks:
            assert task.agent is not None


@pytest.mark.unit
class TestSequentialTasks:
    """Tests for sequential task workflow"""

    def test_create_sequential_tasks(self):
        """Test creating sequential tasks"""
        tasks = create_sequential_tasks("https://github.com/test/repo")
        assert len(tasks) == 3

    def test_sequential_tasks_order(self):
        """Test that tasks are in correct order"""
        tasks = create_sequential_tasks("https://github.com/test/repo")

        # Check agent roles to verify order
        assert tasks[0].agent.role == "Code Analyzer"
        assert tasks[1].agent.role == "Test Planner"
        assert tasks[2].agent.role == "Test Writer"

    def test_sequential_tasks_with_file_path(self):
        """Test creating sequential tasks with file path"""
        tasks = create_sequential_tasks("https://github.com/test/repo", file_path="test.py")
        assert "test.py" in tasks[0].description

    def test_sequential_tasks_with_function_name(self):
        """Test creating sequential tasks with function name"""
        tasks = create_sequential_tasks(
            "https://github.com/test/repo", function_name="test_func"
        )
        assert "test_func" in tasks[0].description

    def test_sequential_tasks_context_chain(self):
        """Test that tasks have context dependencies"""
        tasks = create_sequential_tasks("https://github.com/test/repo")

        # Planning task should have analysis task as context
        assert tasks[0] in tasks[1].context

        # Generation task should have planning task as context
        assert tasks[1] in tasks[2].context


@pytest.mark.unit
class TestTaskDescriptions:
    """Tests for task description quality"""

    def test_analysis_task_mentions_tools(self):
        """Test that analysis task mentions required tools"""
        task = create_analysis_task("https://github.com/test/repo")
        description = task.description.lower()
        assert "github" in description or "fetch" in description
        assert "ast" in description or "parse" in description

    def test_planning_task_mentions_scenarios(self):
        """Test that planning task mentions test scenarios"""
        task = create_planning_task()
        description = task.description.lower()
        assert "scenario" in description or "test case" in description
        assert "edge case" in description or "happy path" in description

    def test_generation_task_mentions_pytest(self):
        """Test that generation task mentions pytest"""
        task = create_test_generation_task()
        description = task.description.lower()
        assert "pytest" in description
        assert "assertion" in description or "assert" in description
