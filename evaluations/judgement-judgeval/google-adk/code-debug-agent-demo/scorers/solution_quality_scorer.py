"""Solution Quality Scorer for debugging agent evaluation."""

import re
from typing import Optional
from judgeval.scorers.example_scorer import ExampleScorer
from src.data_models import DebugAgentExample


class SolutionQualityScorer(ExampleScorer):
    """Evaluates the quality of debugging solutions provided by the agent.

    This scorer assesses whether the agent's response:
    1. Contains relevant solution keywords
    2. Provides actionable fixes
    3. Includes Stack Exchange references or documentation
    4. Explains the root cause of the error
    """

    name: str = "Solution Quality Scorer"
    threshold: float = 0.7

    def __init__(self, threshold: float = 0.7):
        """Initialize the scorer.

        Args:
            threshold: Minimum score required to pass (0.0-1.0)
        """
        super().__init__()
        self.threshold = threshold

    async def a_score_example(self, example: DebugAgentExample) -> float:
        """Score the quality of the agent's debugging solution.

        Args:
            example: Debug agent example with error and response

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        feedback_parts = []

        response_lower = example.agent_response.lower()

        # Check 1: Contains expected solution keywords (0.3 points)
        if example.expected_solution_keywords:
            keywords_found = sum(
                1 for keyword in example.expected_solution_keywords
                if keyword.lower() in response_lower
            )
            keyword_ratio = keywords_found / len(example.expected_solution_keywords)
            score += keyword_ratio * 0.3

            if keyword_ratio >= 0.7:
                feedback_parts.append(
                    f"Contains {keywords_found}/{len(example.expected_solution_keywords)} expected keywords"
                )
            else:
                feedback_parts.append(
                    f"Missing key solution terms ({keywords_found}/{len(example.expected_solution_keywords)})"
                )

        # Check 2: Provides actionable fixes (0.3 points)
        actionable_indicators = [
            "install", "pip install", "npm install", "update", "change",
            "modify", "add", "remove", "fix", "replace", "import",
            "configure", "set", "run", "execute"
        ]
        actions_found = sum(
            1 for indicator in actionable_indicators
            if indicator in response_lower
        )

        if actions_found >= 2:
            score += 0.3
            feedback_parts.append("Provides actionable solution steps")
        elif actions_found == 1:
            score += 0.15
            feedback_parts.append("Provides limited actionable guidance")
        else:
            feedback_parts.append("Lacks actionable solution steps")

        # Check 3: Includes references or documentation (0.2 points)
        has_stackoverflow_link = "stackoverflow.com" in response_lower
        has_documentation_link = any(
            domain in response_lower
            for domain in ["docs.", ".org/docs", "/documentation", "github.com"]
        )

        if has_stackoverflow_link or has_documentation_link:
            score += 0.2
            feedback_parts.append("Includes helpful references")
        else:
            feedback_parts.append("Missing reference links")

        # Check 4: Explains root cause (0.2 points)
        explanation_indicators = [
            "because", "caused by", "due to", "reason", "error occurs when",
            "this happens when", "the issue is", "the problem is"
        ]
        explanations_found = sum(
            1 for indicator in explanation_indicators
            if indicator in response_lower
        )

        if explanations_found >= 2:
            score += 0.2
            feedback_parts.append("Explains the root cause well")
        elif explanations_found == 1:
            score += 0.1
            feedback_parts.append("Provides some explanation")
        else:
            feedback_parts.append("Lacks root cause explanation")

        # Set reason for the score
        self.reason = " | ".join(feedback_parts)

        return min(score, 1.0)
