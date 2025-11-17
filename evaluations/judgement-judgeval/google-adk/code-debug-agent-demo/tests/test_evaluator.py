"""Tests for the evaluation framework."""

import pytest
from src.data_models import DebugAgentExample
from scorers.solution_quality_scorer import SolutionQualityScorer
from scorers.tool_usage_scorer import ToolUsageScorer
from scorers.response_completeness_scorer import ResponseCompletenessScorer


@pytest.mark.asyncio
async def test_solution_quality_scorer_high_quality():
    """Test that high-quality solutions score well."""
    example = DebugAgentExample(
        error_message="ImportError: No module named 'pandas'",
        programming_language="python",
        agent_response="""
        This error occurs because the pandas library is not installed in your environment.

        To fix this, you need to install pandas using pip:

        ```bash
        pip install pandas
        ```

        Alternatively, if you're using conda:

        ```bash
        conda install pandas
        ```

        After installation, you should be able to import pandas successfully.
        For more information, see: https://stackoverflow.com/questions/tagged/pandas
        """,
        tools_called=["search_stack_exchange_for_error"],
        input="ImportError: No module named 'pandas'",
        actual_output="Solution provided",
        expected_solution_keywords=["pip install", "pandas", "install"],
    )

    scorer = SolutionQualityScorer(threshold=0.7)
    score = await scorer.a_score_example(example)

    assert score >= 0.7, f"Expected score >= 0.7, got {score}"
    assert "keywords" in scorer.reason.lower() or "actionable" in scorer.reason.lower()


@pytest.mark.asyncio
async def test_solution_quality_scorer_low_quality():
    """Test that low-quality solutions score poorly."""
    example = DebugAgentExample(
        error_message="ImportError: No module named 'pandas'",
        programming_language="python",
        agent_response="You have an error. Try fixing it.",
        tools_called=[],
        input="ImportError: No module named 'pandas'",
        actual_output="You have an error. Try fixing it.",
        expected_solution_keywords=["pip install", "pandas", "install"],
    )

    scorer = SolutionQualityScorer(threshold=0.7)
    score = await scorer.a_score_example(example)

    assert score < 0.7, f"Expected score < 0.7, got {score}"


@pytest.mark.asyncio
async def test_tool_usage_scorer_correct_tools():
    """Test that using correct tools scores well."""
    example = DebugAgentExample(
        error_message="TypeError: Cannot read property 'map' of undefined",
        programming_language="javascript",
        agent_response="Here's the solution...",
        tools_called=["search_stack_exchange_for_error", "analyze_error_and_suggest_fix"],
        expected_tools=["search_stack_exchange_for_error", "analyze_error_and_suggest_fix"],
        input="TypeError: Cannot read property 'map' of undefined",
        actual_output="Here's the solution...",
    )

    scorer = ToolUsageScorer(threshold=0.8)
    score = await scorer.a_score_example(example)

    assert score >= 0.8, f"Expected score >= 0.8, got {score}"


@pytest.mark.asyncio
async def test_tool_usage_scorer_missing_tools():
    """Test that missing expected tools reduces score."""
    example = DebugAgentExample(
        error_message="TypeError: Cannot read property 'map' of undefined",
        programming_language="javascript",
        agent_response="Here's the solution...",
        tools_called=["search_stack_exchange_general"],  # Wrong tool
        expected_tools=["search_stack_exchange_for_error"],
        input="TypeError: Cannot read property 'map' of undefined",
        actual_output="Here's the solution...",
    )

    scorer = ToolUsageScorer(threshold=0.8)
    score = await scorer.a_score_example(example)

    assert score < 0.8, f"Expected score < 0.8, got {score}"


@pytest.mark.asyncio
async def test_response_completeness_scorer_complete():
    """Test that complete responses score well."""
    example = DebugAgentExample(
        error_message="AttributeError: 'NoneType' object has no attribute 'get'",
        programming_language="python",
        agent_response="""
        This error occurs when you try to call a method on a None object. There are several approaches to fix this:

        **Option 1: Check for None before accessing**
        ```python
        if my_object is not None:
            value = my_object.get('key')
        ```

        **Option 2: Use optional chaining (Python 3.10+)**
        ```python
        value = my_object.get('key') if my_object else None
        ```

        **Option 3: Initialize properly**
        Make sure the object is initialized before use.

        Note: This is a common error when working with APIs that may return None.
        Always validate your data before accessing attributes.

        For more examples, see: https://stackoverflow.com/questions/tagged/nonetype
        """,
        tools_called=["search_stack_exchange_for_error"],
        input="AttributeError: 'NoneType' object has no attribute 'get'",
        actual_output="Solution provided",
    )

    scorer = ResponseCompletenessScorer(threshold=0.7)
    score = await scorer.a_score_example(example)

    assert score >= 0.7, f"Expected score >= 0.7, got {score}"


@pytest.mark.asyncio
async def test_response_completeness_scorer_incomplete():
    """Test that incomplete responses score poorly."""
    example = DebugAgentExample(
        error_message="AttributeError: 'NoneType' object has no attribute 'get'",
        programming_language="python",
        agent_response="Check if object is None.",
        tools_called=[],
        input="AttributeError: 'NoneType' object has no attribute 'get'",
        actual_output="Check if object is None.",
    )

    scorer = ResponseCompletenessScorer(threshold=0.7)
    score = await scorer.a_score_example(example)

    assert score < 0.7, f"Expected score < 0.7, got {score}"


def test_debug_agent_example_creation():
    """Test that DebugAgentExample can be created."""
    example = DebugAgentExample(
        error_message="Test error",
        programming_language="python",
        agent_response="Test response",
        tools_called=["tool1", "tool2"],
        input="Test input",
        actual_output="Test output",
    )

    assert example.error_message == "Test error"
    assert example.programming_language == "python"
    assert len(example.tools_called) == 2
