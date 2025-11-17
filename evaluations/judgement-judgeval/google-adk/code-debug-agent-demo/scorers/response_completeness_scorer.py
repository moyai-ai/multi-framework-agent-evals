"""Response Completeness Scorer for evaluating agent response quality."""

from judgeval.scorers.example_scorer import ExampleScorer
from src.data_models import DebugAgentExample


class ResponseCompletenessScorer(ExampleScorer):
    """Evaluates the completeness of the agent's debugging response.

    This scorer checks:
    1. Response length is adequate
    2. Multiple solution approaches are provided
    3. Code examples are included
    4. Additional context is provided
    """

    name: str = "Response Completeness Scorer"
    threshold: float = 0.7

    def __init__(self, threshold: float = 0.7):
        """Initialize the scorer.

        Args:
            threshold: Minimum score required to pass (0.0-1.0)
        """
        super().__init__()
        self.threshold = threshold

    async def a_score_example(self, example: DebugAgentExample) -> float:
        """Score the completeness of the agent's response.

        Args:
            example: Debug agent example with response

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0
        feedback_parts = []

        response = example.agent_response
        response_lower = response.lower()

        # Check 1: Response length is adequate (0.2 points)
        response_length = len(response)
        if response_length >= 300:
            score += 0.2
            feedback_parts.append("Adequate response length")
        elif response_length >= 150:
            score += 0.1
            feedback_parts.append("Brief response")
        else:
            feedback_parts.append("Response too short")

        # Check 2: Multiple solutions or approaches (0.3 points)
        solution_indicators = [
            "first", "second", "alternatively", "another option",
            "you can also", "option 1", "option 2", "method 1", "method 2",
            "approach 1", "approach 2", "solution 1", "solution 2"
        ]
        has_multiple_solutions = sum(
            1 for indicator in solution_indicators
            if indicator in response_lower
        )

        if has_multiple_solutions >= 2:
            score += 0.3
            feedback_parts.append("Provides multiple solution approaches")
        elif has_multiple_solutions == 1:
            score += 0.15
            feedback_parts.append("Mentions alternative approaches")
        else:
            feedback_parts.append("Single solution only")

        # Check 3: Includes code examples (0.3 points)
        # Look for code indicators like backticks, common keywords, etc.
        code_indicators = [
            "```", "`", "import ", "def ", "function ", "class ",
            "const ", "let ", "var ", "npm install", "pip install"
        ]
        has_code = sum(
            1 for indicator in code_indicators
            if indicator in response
        )

        if has_code >= 3:
            score += 0.3
            feedback_parts.append("Includes code examples")
        elif has_code >= 1:
            score += 0.15
            feedback_parts.append("Some code snippets")
        else:
            feedback_parts.append("No code examples")

        # Check 4: Provides additional context (0.2 points)
        context_indicators = [
            "note:", "warning:", "important:", "tip:", "remember:",
            "be careful", "make sure", "also", "additionally", "furthermore",
            "common cause", "typically", "usually", "often"
        ]
        has_context = sum(
            1 for indicator in context_indicators
            if indicator in response_lower
        )

        if has_context >= 2:
            score += 0.2
            feedback_parts.append("Provides helpful context")
        elif has_context == 1:
            score += 0.1
            feedback_parts.append("Some additional context")
        else:
            feedback_parts.append("Lacks additional context")

        self.reason = " | ".join(feedback_parts)

        return min(score, 1.0)
