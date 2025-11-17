"""Tool Usage Scorer for evaluating agent tool calling behavior."""

from typing import Set
from judgeval.scorers.example_scorer import ExampleScorer
from src.data_models import DebugAgentExample


class ToolUsageScorer(ExampleScorer):
    """Evaluates whether the agent calls the appropriate tools for debugging.

    This scorer checks:
    1. Whether expected tools were called
    2. Whether unnecessary tools were avoided
    3. The efficiency of tool usage
    """

    name: str = "Tool Usage Scorer"
    threshold: float = 0.8

    def __init__(self, threshold: float = 0.8):
        """Initialize the scorer.

        Args:
            threshold: Minimum score required to pass (0.0-1.0)
        """
        super().__init__()
        self.threshold = threshold

    async def a_score_example(self, example: DebugAgentExample) -> float:
        """Score the agent's tool usage.

        Args:
            example: Debug agent example with tools called

        Returns:
            Score between 0.0 and 1.0
        """
        if not example.expected_tools:
            # If no expected tools specified, just check that some tools were used
            if example.tools_called:
                self.reason = f"Agent called {len(example.tools_called)} tool(s): {', '.join(example.tools_called)}"
                return 1.0
            else:
                self.reason = "No tools were called"
                return 0.0

        expected_set: Set[str] = set(example.expected_tools)
        called_set: Set[str] = set(example.tools_called)

        # Calculate metrics
        tools_matched = expected_set.intersection(called_set)
        tools_missed = expected_set - called_set
        tools_extra = called_set - expected_set

        # Scoring
        score = 0.0
        feedback_parts = []

        # Check 1: Expected tools were called (0.7 points)
        if tools_matched:
            match_ratio = len(tools_matched) / len(expected_set)
            score += match_ratio * 0.7
            feedback_parts.append(
                f"Called {len(tools_matched)}/{len(expected_set)} expected tools"
            )
        else:
            feedback_parts.append("Did not call any expected tools")

        # Check 2: No unnecessary tools (0.3 points)
        if not tools_extra:
            score += 0.3
            feedback_parts.append("No unnecessary tool calls")
        else:
            # Partial credit if only a few extra tools
            if len(tools_extra) <= 1:
                score += 0.15
                feedback_parts.append(f"Called 1 extra tool: {list(tools_extra)[0]}")
            else:
                feedback_parts.append(
                    f"Called {len(tools_extra)} unnecessary tools: {', '.join(tools_extra)}"
                )

        # Detailed breakdown
        details = []
        if tools_matched:
            details.append(f"Matched: {', '.join(tools_matched)}")
        if tools_missed:
            details.append(f"Missed: {', '.join(tools_missed)}")
        if tools_extra:
            details.append(f"Extra: {', '.join(tools_extra)}")

        self.reason = " | ".join(feedback_parts) + (
            f" ({'; '.join(details)})" if details else ""
        )

        return min(score, 1.0)
