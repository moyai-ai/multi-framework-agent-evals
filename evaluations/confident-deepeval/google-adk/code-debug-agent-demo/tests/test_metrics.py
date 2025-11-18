from deepeval.test_case import LLMTestCase

from google_adk_deepeval_run.evaluators.metrics import (
    KeywordCoverageMetric,
    LinkPresenceMetric,
    ToolUsageMetric,
)


def test_keyword_metric_detects_missing_terms():
    test_case = LLMTestCase(
        input="Why is pandas missing?",
        actual_output="Install pandas with pip install pandas",
        context=[],
    )
    metric = KeywordCoverageMetric(["pandas", "pip", "import"])

    score = metric.measure(test_case)

    assert score == 0.0
    assert metric.is_successful() is False
    assert "Missing keywords" in metric.reason


def test_tool_metric_validates_expected_tools():
    test_case = LLMTestCase(
        input="error",
        actual_output="response",
        context=[],
    )
    metric = ToolUsageMetric(["search_stack_exchange_for_error"])

    score = metric.measure(test_case, tools_used=["search_stack_exchange_for_error"])

    assert score == 1.0
    assert metric.is_successful() is True


def test_link_metric_handles_empty_expectations():
    test_case = LLMTestCase(
        input="error",
        actual_output="response",
        context=[],
    )
    metric = LinkPresenceMetric([])

    score = metric.measure(test_case)

    assert score == 1.0
    assert metric.reason == "No link expectations provided."
