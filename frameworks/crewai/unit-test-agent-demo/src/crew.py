"""
CrewAI crew configuration for the Unit Test Agent
"""

from crewai import Crew, Process
from typing import Optional
from .agents import (
    create_code_analyzer_agent,
    create_test_planner_agent,
    create_test_writer_agent,
)
from .tasks import create_sequential_tasks
from .context import Config


def create_unit_test_crew(
    repository_url: str,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
    verbose: bool = None,
) -> Crew:
    """
    Creates a CrewAI crew for unit test generation

    Args:
        repository_url: GitHub repository URL to analyze
        file_path: Optional specific file path within the repository
        function_name: Optional specific function to generate tests for
        verbose: Optional verbose flag (uses Config.VERBOSE if not provided)

    Returns:
        Configured Crew instance
    """
    config = Config()
    if verbose is None:
        verbose = config.VERBOSE

    # Create tasks
    tasks = create_sequential_tasks(repository_url, file_path, function_name)

    # Create crew with sequential process
    crew = Crew(
        agents=[
            create_code_analyzer_agent(),
            create_test_planner_agent(),
            create_test_writer_agent(),
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
        memory=False,  # Disable memory for simpler operation
        cache=True,  # Enable caching for efficiency
        max_rpm=10,  # Rate limiting
    )

    return crew


def run_unit_test_generation(
    repository_url: str,
    file_path: Optional[str] = None,
    function_name: Optional[str] = None,
    verbose: bool = None,
) -> dict:
    """
    Convenience function to create and run the unit test crew

    Args:
        repository_url: GitHub repository URL to analyze
        file_path: Optional specific file path within the repository
        function_name: Optional specific function to generate tests for
        verbose: Optional verbose flag

    Returns:
        Dictionary containing crew execution results
    """
    crew = create_unit_test_crew(repository_url, file_path, function_name, verbose)

    # Execute the crew
    result = crew.kickoff()

    return {
        "repository_url": repository_url,
        "file_path": file_path,
        "function_name": function_name,
        "result": result,
        "raw_output": str(result),
    }
