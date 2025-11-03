"""
CrewAI task definitions for the Unit Test Agent workflow
"""

from crewai import Task
from .agents import (
    create_code_analyzer_agent,
    create_test_planner_agent,
    create_test_writer_agent,
)


def create_analysis_task(repository_url: str, file_path: str = None, function_name: str = None) -> Task:
    """
    Creates a task for analyzing Python code

    Args:
        repository_url: GitHub repository URL
        file_path: Optional specific file to analyze
        function_name: Optional specific function to analyze
    """
    description = f"""Fetch and analyze Python code from the repository: {repository_url}"""

    if file_path:
        description += f"\nFocus on file: {file_path}"

    if function_name:
        description += f"\nTarget function: {function_name}"
    else:
        description += "\nExtract all functions from the file(s)"

    description += """

    Use the GitHub Fetcher tool to retrieve the code, then use the AST Parser tool to extract:
    1. Function names and signatures
    2. Parameters with type hints and defaults
    3. Return types
    4. Docstrings
    5. Whether functions are async
    6. Class membership (if methods)
    7. Decorators

    Provide a comprehensive analysis of each function found.
    """

    expected_output = """A detailed report containing:
    - List of functions found
    - Complete function signatures
    - Parameter details with types
    - Return type information
    - Docstring content
    - Source code snippets
    """

    return Task(
        description=description,
        expected_output=expected_output,
        agent=create_code_analyzer_agent(),
    )


def create_planning_task(analysis_context: str = None) -> Task:
    """
    Creates a task for planning test scenarios

    Args:
        analysis_context: Context from the analysis task
    """
    description = """Based on the code analysis, create a comprehensive test plan for each function.

    For each function, design test scenarios that cover:

    1. **Happy Path Cases**: Normal usage with valid inputs
    2. **Edge Cases**: Boundary values, empty inputs, special values (None, 0, "", etc.)
    3. **Error Cases**: Invalid inputs, type errors, exceptions that should be raised
    4. **State Management**: For class methods, test different object states
    5. **Async Handling**: For async functions, test proper async/await behavior

    Structure your test plan with:
    - Test class name (following pytest conventions)
    - List of test scenarios with:
      - Scenario name (descriptive)
      - Description of what is being tested
      - Input values
      - Expected output or exception
      - Any setup/teardown needs
    - Required fixtures
    - Required imports
    - Mocking requirements (if external dependencies exist)

    Make the test plan detailed enough that another developer could implement it.
    """

    if analysis_context:
        description = f"{analysis_context}\n\n{description}"

    expected_output = """A structured test plan for each function containing:
    - Test class name
    - List of test scenarios (minimum 3-5 per function)
    - Each scenario with: name, description, inputs, expected outputs
    - Required fixtures
    - Required imports
    - Mocking strategy if needed
    """

    return Task(
        description=description,
        expected_output=expected_output,
        agent=create_test_planner_agent(),
    )


def create_test_generation_task(plan_context: str = None) -> Task:
    """
    Creates a task for generating pytest code

    Args:
        plan_context: Context from the planning task
    """
    description = """Generate clean, professional pytest code that implements the test plan.

    Follow these pytest best practices:

    1. **Naming**: Use descriptive test names like `test_<function>_<scenario>`
    2. **Structure**: Arrange-Act-Assert pattern
    3. **Fixtures**: Define fixtures for common setup
    4. **Assertions**: Use appropriate pytest assertions
    5. **Parametrization**: Use @pytest.mark.parametrize for similar test cases
    6. **Docstrings**: Add docstrings to test functions explaining what they test
    7. **Mocking**: Use pytest-mock or unittest.mock where needed
    8. **Async**: Use @pytest.mark.asyncio for async tests

    Generate complete, runnable test code including:
    - All necessary imports
    - Fixture definitions
    - Test class (if applicable)
    - All test functions
    - Proper type hints
    - Clear comments

    The generated code should be production-ready and follow PEP 8 style guidelines.
    """

    if plan_context:
        description = f"{plan_context}\n\n{description}"

    expected_output = """Complete pytest test code including:
    - Import statements (pytest, function under test, mocking libraries, etc.)
    - Fixture definitions if needed
    - Test class or functions
    - All test implementations with assertions
    - Proper formatting and comments
    - Code that can be saved directly to a test_*.py file and run
    """

    return Task(
        description=description,
        expected_output=expected_output,
        agent=create_test_writer_agent(),
    )


def create_sequential_tasks(repository_url: str, file_path: str = None, function_name: str = None):
    """
    Creates all three tasks in sequence for a complete test generation workflow

    Args:
        repository_url: GitHub repository URL
        file_path: Optional specific file to analyze
        function_name: Optional specific function to analyze

    Returns:
        List of tasks in execution order
    """
    analysis_task = create_analysis_task(repository_url, file_path, function_name)
    planning_task = create_planning_task()
    generation_task = create_test_generation_task()

    # Set up task dependencies via context
    planning_task.context = [analysis_task]
    generation_task.context = [planning_task]

    return [analysis_task, planning_task, generation_task]
