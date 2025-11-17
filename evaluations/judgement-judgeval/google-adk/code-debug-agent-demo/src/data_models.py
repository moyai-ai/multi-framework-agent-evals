"""Data models for Code Debug Agent evaluation."""

from typing import List, Optional
from pydantic import Field
from judgeval.data import Example


class DebugAgentExample(Example):
    """Example for debugging agent evaluation.

    This model extends JudgmentLabs' Example class with fields specific
    to code debugging scenarios.
    """

    error_message: str = Field(
        description="The error message or stack trace to debug"
    )
    programming_language: Optional[str] = Field(
        default=None,
        description="Programming language of the error (e.g., python, javascript)"
    )
    framework: Optional[str] = Field(
        default=None,
        description="Framework involved in the error (e.g., react, django)"
    )
    agent_response: str = Field(
        description="The agent's complete response to the error"
    )
    tools_called: List[str] = Field(
        default_factory=list,
        description="List of tools the agent called during execution"
    )
    expected_tools: Optional[List[str]] = Field(
        default=None,
        description="Expected tools the agent should call"
    )
    expected_solution_keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords that should appear in a good solution"
    )
    retrieval_context: Optional[List[str]] = Field(
        default=None,
        description="Stack Exchange results or other context retrieved"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="Time taken to execute the agent (seconds)"
    )

    # Additional metadata for specific error types
    error_type: Optional[str] = Field(
        default=None,
        description="Category of error (e.g., ImportError, TypeError, SyntaxError)"
    )
    severity: Optional[str] = Field(
        default="medium",
        description="Error severity: low, medium, high, critical"
    )


class CodeQualityExample(Example):
    """Example for code quality evaluation."""

    code_input: str = Field(
        description="Original code or error context"
    )
    agent_output: str = Field(
        description="Agent's analysis or suggested fix"
    )
    programming_language: str = Field(
        description="Programming language"
    )
    quality_aspects: List[str] = Field(
        default_factory=list,
        description="Aspects to evaluate (e.g., correctness, clarity, security)"
    )


class ToolUsageExample(Example):
    """Example for evaluating tool usage patterns."""

    query: str = Field(
        description="User's query or error message"
    )
    tools_available: List[str] = Field(
        description="Tools available to the agent"
    )
    tools_used: List[str] = Field(
        description="Tools actually used by the agent"
    )
    tool_sequence: List[str] = Field(
        default_factory=list,
        description="Order in which tools were called"
    )
    expected_tools: Optional[List[str]] = Field(
        default=None,
        description="Expected tools for this scenario"
    )
    tool_outputs: Optional[dict] = Field(
        default=None,
        description="Outputs from each tool call"
    )
