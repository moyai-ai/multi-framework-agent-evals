"""Main evaluation runner using JudgmentLabs."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from dotenv import load_dotenv
from judgeval import JudgmentClient
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.agent_wrapper import DebugAgentRunner
from src.data_models import DebugAgentExample
from scorers.response_completeness_scorer import ResponseCompletenessScorer
from scorers.solution_quality_scorer import SolutionQualityScorer
from scorers.tool_usage_scorer import ToolUsageScorer

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()


class DebugAgentEvaluator:
    """Evaluator for the Code Debug Agent using JudgmentLabs."""

    def __init__(
        self,
        agent_name: str = "debug_agent",
        project_name: str = "code-debug-agent-eval",
        output_dir: str = "./reports",  # Changed from "./eval_results"
        use_langfuse: bool = False,
        use_langsmith: bool = False,
    ):
        """Initialize the evaluator.

        Args:
            agent_name: Name of the agent to evaluate
            project_name: JudgmentLabs project name
            output_dir: Directory to save evaluation results
            use_langfuse: Enable Langfuse tracing for agent runs
            use_langsmith: Enable LangSmith tracing for agent runs
        """
        if use_langfuse and use_langsmith:
            raise ValueError("Cannot enable both Langfuse and LangSmith tracing")

        self.agent_name = agent_name
        self.project_name = project_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_langfuse = use_langfuse
        self.use_langsmith = use_langsmith

        # Initialize JudgmentLabs client
        self.judgment_client = JudgmentClient(
            api_key=os.getenv("JUDGMENT_API_KEY"),
            organization_id=os.getenv("JUDGMENT_ORG_ID"),
        )

        # Initialize agent runner
        self.agent_runner = DebugAgentRunner(
            agent_name=agent_name,
            use_langfuse=use_langfuse,
            use_langsmith=use_langsmith,
        )

    async def run_scenario(
        self,
        scenario: Dict[str, Any],
    ) -> DebugAgentExample:
        """Run a single scenario and collect results.

        Args:
            scenario: Scenario dictionary with error_message, language, etc.

        Returns:
            DebugAgentExample with execution results
        """
        console.print(f"[cyan]Running scenario:[/cyan] {scenario.get('name', 'Unnamed')}")

        # Extract scenario details
        error_message = scenario["error_message"]
        programming_language = scenario.get("programming_language")
        framework = scenario.get("framework")
        conversation = scenario.get("conversation") or []
        expected_tools = scenario.get("expected_tools") or self._aggregate_conversation_field(
            conversation, "expected_tools"
        )
        expected_keywords = scenario.get("expected_keywords") or self._aggregate_conversation_field(
            conversation, "expected_keywords"
        )

        # Run the agent
        example = await self.agent_runner.run_debug_query(
            error_message=error_message,
            programming_language=programming_language,
            framework=framework,
            expected_tools=expected_tools,
            expected_keywords=expected_keywords,
            conversation=conversation,
        )

        return example

    async def evaluate_examples(
        self,
        examples: List[DebugAgentExample],
        eval_run_name: Optional[str] = None,
        assert_test: bool = False,
    ) -> List[Any]:
        """Evaluate examples using JudgmentLabs scorers.

        Args:
            examples: List of examples to evaluate
            eval_run_name: Name for this evaluation run
            assert_test: Whether to raise exception on failure

        Returns:
            List of evaluation results
        """
        if not eval_run_name:
            eval_run_name = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        console.print(f"\n[yellow]Evaluating {len(examples)} examples...[/yellow]")

        # Configure scorers
        scorers = [
            SolutionQualityScorer(threshold=0.7),
            ToolUsageScorer(threshold=0.8),
            ResponseCompletenessScorer(threshold=0.7),
        ]

        # Run evaluation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running evaluation...", total=None)

            results = self.judgment_client.run_evaluation(
                examples=examples,
                scorers=scorers,
                project_name=self.project_name,
                eval_run_name=eval_run_name,
                assert_test=assert_test,
            )

            progress.update(task, completed=True)

        return results

    def display_results(self, results: List[Any], examples: List[DebugAgentExample]):
        """Display evaluation results in a formatted table.

        Args:
            results: Evaluation results from JudgmentLabs
            examples: Original examples
        """
        console.print("\n[bold green]Evaluation Results[/bold green]\n")

        # Summary table
        summary_table = Table(title="Overall Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")

        total = len(results)
        passed = sum(1 for r in results if r.success)
        pass_rate = (passed / total * 100) if total > 0 else 0

        summary_table.add_row("Total Examples", str(total))
        summary_table.add_row("Passed", str(passed))
        summary_table.add_row("Failed", str(total - passed))
        summary_table.add_row("Pass Rate", f"{pass_rate:.1f}%")

        console.print(summary_table)
        console.print()

        # Detailed results table
        details_table = Table(title="Detailed Results")
        details_table.add_column("Scenario", style="cyan", no_wrap=False, max_width=30)
        details_table.add_column("Error Type", style="yellow")
        details_table.add_column("Overall", style="green")
        details_table.add_column("Quality", style="blue")
        details_table.add_column("Tools", style="magenta")
        details_table.add_column("Completeness", style="cyan")

        for i, (result, example) in enumerate(zip(results, examples)):
            scenario_name = f"Scenario {i+1}"
            error_type = example.error_type or "Unknown"

            # Extract scores
            scores = {}
            for scorer_data in result.scorers_data:
                scorer_name = scorer_data.name
                score = scorer_data.score
                passed = "✓" if scorer_data.success else "✗"

                if "Quality" in scorer_name:
                    scores["quality"] = f"{passed} {score:.2f}"
                elif "Tool" in scorer_name:
                    scores["tools"] = f"{passed} {score:.2f}"
                elif "Completeness" in scorer_name:
                    scores["completeness"] = f"{passed} {score:.2f}"

            overall = "✓ PASS" if result.success else "✗ FAIL"

            details_table.add_row(
                scenario_name,
                error_type,
                overall,
                scores.get("quality", "N/A"),
                scores.get("tools", "N/A"),
                scores.get("completeness", "N/A"),
            )

        console.print(details_table)

    @staticmethod
    def _aggregate_conversation_field(
        conversation: Iterable[Dict[str, Any]],
        field_name: str,
    ) -> Optional[List[str]]:
        """Collect unique values for a field across conversation turns."""
        collected: List[str] = []
        for turn in conversation:
            values = turn.get(field_name) or []
            for value in values:
                if value not in collected:
                    collected.append(value)
        return collected or None

    def save_results(
        self,
        results: List[Any],
        examples: List[DebugAgentExample],
        eval_run_name: str,
    ):
        """Save evaluation results to JSON file.

        Args:
            results: Evaluation results
            examples: Original examples
            eval_run_name: Name of the evaluation run
        """
        output_file = self.output_dir / f"{eval_run_name}.json"

        # Prepare output data
        output_data = {
            "eval_run_name": eval_run_name,
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.agent_name,
            "project_name": self.project_name,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
            },
            "results": [],
        }

        for i, (result, example) in enumerate(zip(results, examples)):
            result_data = {
                "scenario_index": i,
                "error_message": example.error_message,
                "error_type": example.error_type,
                "programming_language": example.programming_language,
                "framework": example.framework,
                "success": result.success,
                "execution_time": example.execution_time,
                "tools_called": example.tools_called,
                "expected_tools": example.expected_tools,
                "scorers": [],
            }

            for scorer_data in result.scorers_data:
                result_data["scorers"].append({
                    "name": scorer_data.name,
                    "score": scorer_data.score,
                    "threshold": scorer_data.threshold,
                    "passed": scorer_data.success,
                    "reason": scorer_data.reason,
                })

            output_data["results"].append(result_data)

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)

        console.print(f"\n[green]Results saved to:[/green] {output_file}")

    async def run_evaluation_from_file(
        self,
        scenario_file: str,
        eval_run_name: Optional[str] = None,
        assert_test: bool = False,
    ):
        """Run evaluation from a scenario file.

        Args:
            scenario_file: Path to JSON file with scenarios
            eval_run_name: Name for this evaluation run
            assert_test: Whether to raise exception on failure
        """
        console.print(f"[bold]Loading scenarios from:[/bold] {scenario_file}\n")

        # Load scenarios
        with open(scenario_file, "r") as f:
            data = json.load(f)

        scenarios: List[Dict[str, Any]]
        if isinstance(data, dict) and "scenarios" in data:
            scenarios = data["scenarios"]
        elif isinstance(data, list):
            scenarios = data
        else:
            scenarios = [data]

        console.print(f"Found {len(scenarios)} scenario(s)\n")

        # Run scenarios
        if not self.agent_runner.session:
            await self.agent_runner.setup()

        examples = []
        for scenario in scenarios:
            try:
                example = await self.run_scenario(scenario)
                examples.append(example)
            except Exception as e:
                logger.error(f"Error running scenario: {e}", exc_info=True)
                console.print(f"[red]Error:[/red] {e}")

        if not examples:
            console.print("[red]No examples to evaluate![/red]")
            return

        # Evaluate
        if not eval_run_name:
            eval_run_name = Path(scenario_file).stem

        results = await self.evaluate_examples(
            examples=examples,
            eval_run_name=eval_run_name,
            assert_test=assert_test,
        )

        # Display and save results
        self.display_results(results, examples)
        self.save_results(results, examples, eval_run_name)


async def async_main():
    """Async main entry point for evaluation."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Code Debug Agent")
    parser.add_argument(
        "scenario_file",
        nargs="?",
        help="Path to scenario JSON file"
    )
    parser.add_argument(
        "--agent",
        default="debug_agent",
        help="Agent name (debug_agent, quick_debug_agent, etc.)"
    )
    parser.add_argument(
        "--project",
        default="code-debug-agent-eval",
        help="JudgmentLabs project name"
    )
    parser.add_argument(
        "--run-name",
        help="Evaluation run name (default: based on scenario file)"
    )
    parser.add_argument(
        "--assert-test",
        action="store_true",
        help="Raise exception if evaluation fails"
    )
    parser.add_argument(
        "--output-dir",
        default="./reports",
        help="Output directory for results"
    )
    parser.add_argument(
        "--all-scenarios",
        action="store_true",
        help="Run every JSON file in the scenarios directory"
    )
    parser.add_argument(
        "--scenarios-dir",
        default="scenarios",
        help="Directory containing scenario JSON files (used with --all-scenarios)"
    )
    parser.add_argument(
        "--use-langfuse",
        action="store_true",
        help="Enable Langfuse tracing for agent executions"
    )
    parser.add_argument(
        "--use-langsmith",
        action="store_true",
        help="Enable LangSmith tracing for agent executions"
    )

    args = parser.parse_args()

    if args.use_langfuse and args.use_langsmith:
        parser.error("Cannot enable both --use-langfuse and --use-langsmith")

    scenario_paths: List[Path] = []
    if args.all_scenarios:
        scenarios_dir = Path(args.scenarios_dir)
        if not scenarios_dir.exists() or not scenarios_dir.is_dir():
            parser.error(f"Scenarios directory not found: {scenarios_dir}")
        scenario_paths = sorted(scenarios_dir.glob("*.json"))
        if not scenario_paths:
            parser.error(f"No scenario files found in {scenarios_dir}")
    elif args.scenario_file:
        scenario_paths = [Path(args.scenario_file)]
    else:
        parser.error("You must provide a scenario_file or use --all-scenarios")

    # Create evaluator
    evaluator = DebugAgentEvaluator(
        agent_name=args.agent,
        project_name=args.project,
        output_dir=args.output_dir,
        use_langfuse=args.use_langfuse,
        use_langsmith=args.use_langsmith,
    )

    for scenario_path in scenario_paths:
        console.print(f"\n[bold]Running scenarios from:[/bold] {scenario_path}\n")

        run_name = args.run_name
        if args.all_scenarios:
            run_name = f"{args.run_name}_{scenario_path.stem}" if args.run_name else None

        await evaluator.run_evaluation_from_file(
            scenario_file=str(scenario_path),
            eval_run_name=run_name,
            assert_test=args.assert_test,
        )


def main():
    """Console script entry point (synchronous wrapper for async_main)."""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
