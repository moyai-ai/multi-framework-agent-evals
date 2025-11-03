"""
CrewAI agent definitions for the Unit Test Agent
"""

from crewai import Agent
from .tools import (
    github_fetcher_tool,
    ast_parser_tool,
    test_plan_generator_tool,
    test_code_generator_tool,
)


def create_code_analyzer_agent() -> Agent:
    """
    Creates the Code Analyzer Agent responsible for fetching and analyzing Python code
    """
    return Agent(
        role="Code Analyzer",
        goal="Fetch Python code from GitHub repositories and extract detailed function information using AST parsing",
        backstory="""You are an expert code analyst with deep knowledge of Python's abstract syntax tree (AST).
        Your specialty is understanding code structure, extracting function signatures, parameters, type hints,
        and dependencies. You provide accurate and detailed information about functions that will be used
        to generate comprehensive unit tests.""",
        tools=[github_fetcher_tool, ast_parser_tool],
        verbose=True,
        allow_delegation=False,
    )


def create_test_planner_agent() -> Agent:
    """
    Creates the Test Planner Agent responsible for designing test strategies
    """
    return Agent(
        role="Test Planner",
        goal="Create comprehensive test plans with scenarios covering happy paths, edge cases, and error conditions",
        backstory="""You are a seasoned QA engineer and test architect with expertise in test-driven development.
        You excel at identifying edge cases, boundary conditions, and potential failure modes. Your test plans
        are thorough, well-organized, and cover all critical scenarios. You understand pytest conventions and
        best practices for writing maintainable tests.""",
        tools=[test_plan_generator_tool],
        verbose=True,
        allow_delegation=False,
    )


def create_test_writer_agent() -> Agent:
    """
    Creates the Test Writer Agent responsible for generating pytest code
    """
    return Agent(
        role="Test Writer",
        goal="Generate clean, well-documented pytest code that implements test plans with proper assertions and fixtures",
        backstory="""You are a Python testing expert who writes elegant, maintainable test code. You follow pytest
        best practices, use appropriate fixtures, and write clear assertions. Your tests are self-documenting
        with descriptive names and include helpful comments. You understand mocking, parameterization, and
        async testing patterns.""",
        tools=[test_code_generator_tool],
        verbose=True,
        allow_delegation=False,
    )


# Agent registry for easy access
AGENTS = {
    "code_analyzer": create_code_analyzer_agent,
    "test_planner": create_test_planner_agent,
    "test_writer": create_test_writer_agent,
}


def get_agent_by_name(name: str) -> Agent:
    """Get an agent by name"""
    if name in AGENTS:
        return AGENTS[name]()
    # Try partial match
    for agent_name, agent_func in AGENTS.items():
        if name.lower() in agent_name.lower():
            return agent_func()
    return None


def list_agents():
    """List all available agents"""
    return [
        {
            "name": "code_analyzer",
            "role": "Code Analyzer",
            "description": "Fetches and analyzes Python code from repositories",
        },
        {
            "name": "test_planner",
            "role": "Test Planner",
            "description": "Creates comprehensive test plans with scenarios",
        },
        {
            "name": "test_writer",
            "role": "Test Writer",
            "description": "Generates pytest code implementing test plans",
        },
    ]
