"""Custom Deepeval metrics tailored to the Code Debug Agent scenarios."""

from __future__ import annotations

from typing import List, Sequence

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class KeywordCoverageMetric(BaseMetric):
    """Checks that every expected keyword appears in the agent response."""

    def __init__(self, keywords: Sequence[str], threshold: float = 1.0):
        self.keywords = [kw.strip() for kw in keywords if kw]
        self.threshold = threshold
        self.async_mode = False
        self.include_reason = True
        self.score = 1.0
        self.success = True

    def measure(self, test_case: LLMTestCase, **_) -> float:
        if not self.keywords:
            self.score = 1.0
            self.success = True
            self.reason = "No keyword expectations provided."
            return self.score

        output = (test_case.actual_output or "").lower()
        missing = [kw for kw in self.keywords if kw.lower() not in output]

        if missing:
            self.score = 0.0
            self.success = False
            self.reason = f"Missing keywords: {', '.join(missing)}"
        else:
            self.score = 1.0
            self.success = True
            self.reason = "All expected keywords detected."

        return self.score

    async def a_measure(self, test_case: LLMTestCase, **kwargs) -> float:
        return self.measure(test_case, **kwargs)

    def is_successful(self) -> bool:
        return bool(self.success)

    @property
    def __name__(self) -> str:
        return "KeywordCoverage"


class LinkPresenceMetric(BaseMetric):
    """Validates that the response references required links."""

    def __init__(self, links: Sequence[str], threshold: float = 1.0):
        self.links = [link for link in links if link]
        self.threshold = threshold
        self.async_mode = False
        self.include_reason = True
        self.score = 1.0
        self.success = True

    def measure(self, test_case: LLMTestCase, **_) -> float:
        if not self.links:
            self.score = 1.0
            self.success = True
            self.reason = "No link expectations provided."
            return self.score

        output = test_case.actual_output or ""
        missing = [link for link in self.links if link not in output]

        if missing:
            self.score = 0.0
            self.success = False
            self.reason = f"Missing links: {', '.join(missing)}"
        else:
            self.score = 1.0
            self.success = True
            self.reason = "All expected links referenced."

        return self.score

    async def a_measure(self, test_case: LLMTestCase, **kwargs) -> float:
        return self.measure(test_case, **kwargs)

    def is_successful(self) -> bool:
        return bool(self.success)

    @property
    def __name__(self) -> str:
        return "LinkPresence"


class ToolUsageMetric(BaseMetric):
    """Ensures the agent invoked the expected Stack Exchange tools."""

    def __init__(self, expected_tools: Sequence[str], threshold: float = 1.0):
        self.expected_tools = [tool for tool in expected_tools if tool]
        self.threshold = threshold
        self.async_mode = False
        self.include_reason = True
        self.score = 1.0
        self.success = True

    def measure(
        self,
        test_case: LLMTestCase,  # noqa: ARG002
        *,
        tools_used: Sequence[str] | None = None,
    ) -> float:
        if not self.expected_tools:
            self.score = 1.0
            self.success = True
            self.reason = "No tool expectations provided."
            return self.score

        tools_used = tools_used or []
        missing = [tool for tool in self.expected_tools if tool not in tools_used]

        if missing:
            self.score = 0.0
            self.success = False
            self.reason = f"Missing tool calls: {', '.join(missing)}"
        else:
            self.score = 1.0
            self.success = True
            self.reason = "All expected tools were invoked."

        return self.score

    async def a_measure(self, test_case: LLMTestCase, **kwargs) -> float:
        return self.measure(test_case, **kwargs)

    def is_successful(self) -> bool:
        return bool(self.success)

    @property
    def __name__(self) -> str:
        return "ToolUsage"


def build_metrics_for_expectations(
    keywords: Sequence[str] | None = None,
    links: Sequence[str] | None = None,
    tools: Sequence[str] | None = None,
) -> List[BaseMetric]:
    metrics: List[BaseMetric] = []

    if keywords:
        metrics.append(KeywordCoverageMetric(keywords))
    if links:
        metrics.append(LinkPresenceMetric(links))
    if tools:
        metrics.append(ToolUsageMetric(tools))

    return metrics


__all__ = [
    "KeywordCoverageMetric",
    "LinkPresenceMetric",
    "ToolUsageMetric",
    "build_metrics_for_expectations",
]
