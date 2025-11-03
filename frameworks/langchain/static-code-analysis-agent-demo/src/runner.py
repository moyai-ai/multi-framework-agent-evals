"""
Scenario Runner

Executes analysis scenarios from JSON files and validates results.
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from src.agent import run_agent
from src.context import Config
from src.manager import AnalysisManager


@dataclass
class ConversationTurn:
    """A single turn in a test conversation."""
    user: str
    expected: Dict[str, Any]
    actual_response: Optional[str] = None
    actions_taken: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    success: bool = False
    error: Optional[str] = None


@dataclass
class Scenario:
    """A complete test scenario."""
    name: str
    description: str
    initial_context: Dict[str, Any]
    conversation: List[ConversationTurn]
    test_files: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    results: Optional[Dict[str, Any]] = None


class ScenarioRunner:
    """Runs analysis scenarios and evaluates results."""

    def __init__(self, verbose: bool = True):
        """
        Initialize the scenario runner.

        Args:
            verbose: Whether to print detailed output
        """
        self.verbose = verbose
        self.manager = AnalysisManager(verbose=verbose)
        self.scenarios_dir = Path("src/scenarios")
        self.results: List[Dict[str, Any]] = []

    def load_scenarios(self) -> List[Scenario]:
        """Load all scenarios from the scenarios directory."""
        scenarios = []

        for scenario_file in self.scenarios_dir.glob("*.json"):
            with open(scenario_file, "r") as f:
                data = json.load(f)

                # Create conversation turns
                conversation = []
                for turn_data in data.get("conversation", []):
                    conversation.append(ConversationTurn(
                        user=turn_data["user"],
                        expected=turn_data.get("expected", {})
                    ))

                scenario = Scenario(
                    name=data["name"],
                    description=data["description"],
                    initial_context=data["initial_context"],
                    conversation=conversation,
                    test_files=data.get("test_files"),
                    metadata=data.get("metadata", {})
                )
                scenarios.append(scenario)

        return scenarios

    async def run_scenario(self, scenario: Scenario, save_individual_report: bool = True) -> Dict[str, Any]:
        """
        Run a single analysis scenario.

        Args:
            scenario: Scenario configuration
            save_individual_report: Whether to save individual report for this scenario

        Returns:
            Results dictionary with execution details
        """
        name = scenario.name
        description = scenario.description

        self._log(f"\n{'=' * 60}")
        self._log(f"Running Scenario: {name}")
        self._log(f"Description: {description}")
        self._log(f"{'=' * 60}")

        start_time = time.time()

        try:
            # Get repository and analysis type from initial context
            repository_url = scenario.initial_context.get("repository_url", "")
            analysis_type = scenario.initial_context.get("analysis_type", "security")

            if not repository_url:
                return {
                    "name": name,
                    "success": False,
                    "error": "No repository URL provided in scenario",
                }

            # Run the analysis
            result = await self.manager.analyze_repository(
                repository_url=repository_url,
                analysis_type=analysis_type,
            )

            execution_time = time.time() - start_time

            # Evaluate results against expectations
            evaluation = self._evaluate_results(scenario, result)

            # Compile results
            scenario_result = {
                "name": name,
                "success": not result.get("error"),
                "repository": repository_url,
                "analysis_type": analysis_type,
                "execution_time": execution_time,
                "files_analyzed": len(result.get("files_analyzed", [])),
                "issues_found": len(result.get("issues_found", [])),
                "steps_taken": result.get("steps_taken", 0),
                "final_report": result.get("final_report", ""),
                "evaluation": evaluation,
                "error": result.get("error"),
            }

            self._log(f"\nScenario '{name}' completed in {execution_time:.2f} seconds")
            self._log(f"Success: {scenario_result['success']}")

            if scenario_result["success"] and "evaluation" in scenario_result:
                self._log(f"Evaluation passed: {evaluation['passed']}")
                self._log(f"Score: {evaluation['score']:.2%}")

            # Save individual report if requested
            if save_individual_report and scenario_result["success"]:
                self._save_individual_report(name, scenario_result)

            return scenario_result

        except Exception as e:
            return {
                "name": name,
                "success": False,
                "repository": scenario.initial_context.get("repository_url", ""),
                "error": str(e),
                "execution_time": time.time() - start_time,
            }

    async def run_scenarios_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Run scenarios from a JSON file.

        Args:
            file_path: Path to the JSON file containing scenario

        Returns:
            List of results for the scenario
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self._log(f"Error: File not found: {file_path}")
            return []

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self._log(f"Error parsing JSON file: {e}")
            return []

        # Create scenario from JSON
        conversation = []
        for turn_data in data.get("conversation", []):
            conversation.append(ConversationTurn(
                user=turn_data["user"],
                expected=turn_data.get("expected", {})
            ))

        scenario = Scenario(
            name=data["name"],
            description=data["description"],
            initial_context=data["initial_context"],
            conversation=conversation,
            test_files=data.get("test_files"),
            metadata=data.get("metadata", {})
        )

        self._log(f"Loaded scenario from {file_path}")

        # Run scenario
        result = await self.run_scenario(scenario)
        self.results.append(result)

        return [result]

    async def run_all_scenarios(self, directory: str = "src/scenarios") -> List[Dict[str, Any]]:
        """
        Run all scenarios in a directory.

        Args:
            directory: Directory containing scenario JSON files

        Returns:
            List of all results
        """
        directory = Path(directory)

        if not directory.exists():
            self._log(f"Error: Directory not found: {directory}")
            return []

        scenario_files = list(directory.glob("*.json"))
        self._log(f"Found {len(scenario_files)} scenario file(s) in {directory}")

        all_results = []
        for file_path in scenario_files:
            self._log(f"\nProcessing file: {file_path}")
            results = await self.run_scenarios_from_file(str(file_path))
            all_results.extend(results)

        return all_results

    async def run_specific_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Run a specific scenario by name.

        Args:
            scenario_name: Name of the scenario to run

        Returns:
            Result dictionary
        """
        scenarios = self.load_scenarios()

        for scenario in scenarios:
            if scenario.name.lower() == scenario_name.lower():
                result = await self.run_scenario(scenario)
                self.results.append(result)
                return result

        raise ValueError(f"Scenario '{scenario_name}' not found")

    def _evaluate_results(
        self, scenario: Scenario, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate analysis results against expectations.

        Args:
            scenario: Scenario with expectations
            result: Analysis result

        Returns:
            Evaluation results with score and details
        """
        checks = []
        score = 0
        max_score = 0

        # Get expectations from first conversation turn (simplified for now)
        if not scenario.conversation:
            return {
                "passed": True,
                "score": 1.0,
                "checks": [],
                "total_checks": 0,
                "passed_checks": 0,
            }

        expectations = scenario.conversation[0].expected

        # Check if expected findings were detected
        if "findings" in expectations:
            max_score += 1
            issues_found = result.get("issues_found", [])
            found_types = [issue.get("rule_id", "") for issue in issues_found]
            expected_findings = expectations["findings"]
            missing = [f for f in expected_findings if f not in found_types]
            passed = len(missing) == 0
            if passed:
                score += 1
            checks.append({
                "check": "expected_findings",
                "expected": expected_findings,
                "found": found_types,
                "missing": missing,
                "passed": passed,
            })

        # Check for required keywords in report
        if "message_contains" in expectations:
            max_score += 1
            keywords = expectations["message_contains"]
            report_lower = result.get("final_report", "").lower()
            found = [kw for kw in keywords if kw.lower() in report_lower]
            missing = [kw for kw in keywords if kw.lower() not in report_lower]
            passed = len(missing) == 0
            if passed:
                score += 1
            checks.append({
                "check": "required_keywords",
                "expected": keywords,
                "found": found,
                "missing": missing,
                "passed": passed,
            })

        # Check severity levels
        if "severity_contains" in expectations:
            max_score += 1
            issues_found = result.get("issues_found", [])
            severities = [issue.get("severity", "") for issue in issues_found]
            expected_severities = expectations["severity_contains"]
            missing = [s for s in expected_severities if s not in severities]
            passed = len(missing) == 0
            if passed:
                score += 1
            checks.append({
                "check": "severity_levels",
                "expected": expected_severities,
                "found": severities,
                "missing": missing,
                "passed": passed,
            })

        return {
            "passed": score == max_score if max_score > 0 else True,
            "score": score / max_score if max_score > 0 else 1.0,
            "checks": checks,
            "total_checks": len(checks),
            "passed_checks": score,
        }

    def _validate_expectations(self, turn: ConversationTurn, response: Dict[str, Any]) -> bool:
        """
        Validate a conversation turn against expectations.

        Args:
            turn: Conversation turn with expectations
            response: Agent response to validate

        Returns:
            True if all expectations are met, False otherwise
        """
        expectations = turn.expected

        # Check actions
        if "actions" in expectations:
            expected_actions = expectations["actions"]
            actual_actions = turn.actions_taken
            if not all(action in actual_actions for action in expected_actions):
                return False

        # Check findings
        if "findings" in expectations:
            expected_findings = expectations["findings"]
            issues = response.get("issues_found", [])
            found_rules = [issue.get("rule_id", "") for issue in issues]
            if not all(finding in found_rules for finding in expected_findings):
                return False

        # Check message contains
        if "message_contains" in expectations:
            keywords = expectations["message_contains"]
            message = response.get("final_report", turn.actual_response or "")
            if not all(kw.lower() in message.lower() for kw in keywords):
                return False

        # Check severity
        if "severity_contains" in expectations:
            expected_severities = expectations["severity_contains"]
            issues = response.get("issues_found", [])
            found_severities = [issue.get("severity", "") for issue in issues]
            if not all(sev in found_severities for sev in expected_severities):
                return False

        return True

    def _calculate_metrics(self, scenario: Scenario, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics for a scenario execution.

        Args:
            scenario: The scenario that was executed
            results: The execution results

        Returns:
            Dictionary of calculated metrics
        """
        turns = results.get("turns", [])
        total_turns = len(turns)
        successful_turns = sum(1 for t in turns if t.get("success", False))

        return {
            "total_turns": total_turns,
            "successful_turns": successful_turns,
            "success_rate": successful_turns / total_turns if total_turns > 0 else 0,
            "total_findings": sum(t.get("findings_count", 0) for t in turns),
            "total_actions": sum(len(t.get("actions", [])) for t in turns),
            "execution_time": results.get("execution_time", 0),
        }

    def _generate_summary(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of all scenario results.

        Args:
            all_results: List of all scenario results

        Returns:
            Summary dictionary with aggregated metrics
        """
        total = len(all_results)
        successful = sum(1 for r in all_results if r.get("success", False))

        return {
            "total_scenarios": total,
            "successful_scenarios": successful,
            "failed_scenarios": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "total_execution_time": sum(r.get("execution_time", 0) for r in all_results),
            "average_execution_time": sum(r.get("execution_time", 0) for r in all_results) / total if total > 0 else 0,
        }

    def _save_individual_report(self, scenario_name: str, result: Dict[str, Any]) -> None:
        """
        Save individual report for a scenario.

        Args:
            scenario_name: Name of the scenario
            result: Result dictionary containing the report
        """
        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Generate filename from scenario name (sanitize it)
        safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in scenario_name)
        safe_name = safe_name.replace(" ", "_").lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{safe_name}_{timestamp}.json"

        report_path = reports_dir / report_filename

        # Create report data
        report_data = {
            "metadata": {
                "scenario_name": scenario_name,
                "execution_time": datetime.now().isoformat(),
                "repository": result.get("repository", ""),
                "analysis_type": result.get("analysis_type", ""),
                "execution_duration": result.get("execution_time", 0),
            },
            "report": result.get("final_report", ""),
            "evaluation": result.get("evaluation", {}),
            "metrics": {
                "files_analyzed": result.get("files_analyzed", 0),
                "issues_found": result.get("issues_found", 0),
                "steps_taken": result.get("steps_taken", 0),
            },
            "error": result.get("error"),
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        self._log(f"Individual report saved to: {report_path}")

    def save_results(self, output_path: str = "scenario_results.json") -> None:
        """
        Save aggregated results to a JSON file.

        Args:
            output_path: Path to save the results file
        """
        # Create a copy of results without the full_report field for summary
        summary_results = []
        for r in self.results:
            summary = {k: v for k, v in r.items() if k != "final_report"}
            summary_results.append(summary)

        output_data = {
            "execution_time": datetime.now().isoformat(),
            "total_scenarios": len(self.results),
            "results": summary_results,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        self._log(f"\nSummary results saved to: {output_path}")

    def print_summary(self) -> None:
        """Print a summary of all scenario results."""
        if not self.results:
            self._log("No scenarios have been run yet.")
            return

        print("\n" + "=" * 60)
        print("SCENARIO EXECUTION SUMMARY")
        print("=" * 60)

        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        failed = total - successful

        print(f"Total Scenarios: {total}")
        print(f"Successful: {successful} ({successful/total:.1%})")
        print(f"Failed: {failed} ({failed/total:.1%})")

        # Calculate average metrics
        if successful > 0:
            avg_time = sum(r.get("execution_time", 0) for r in self.results if r.get("success")) / successful
            avg_files = sum(r.get("files_analyzed", 0) for r in self.results if r.get("success")) / successful
            avg_issues = sum(r.get("issues_found", 0) for r in self.results if r.get("success")) / successful

            print(f"\nAverage Metrics (successful scenarios):")
            print(f"  Execution Time: {avg_time:.2f} seconds")
            print(f"  Files Analyzed: {avg_files:.1f}")
            print(f"  Issues Found: {avg_issues:.1f}")

        # Show evaluation scores
        evaluated = [r for r in self.results if "evaluation" in r]
        if evaluated:
            avg_score = sum(r["evaluation"]["score"] for r in evaluated) / len(evaluated)
            perfect = sum(1 for r in evaluated if r["evaluation"]["passed"])
            print(f"\nEvaluation Results:")
            print(f"  Average Score: {avg_score:.1%}")
            print(f"  Perfect Scores: {perfect}/{len(evaluated)}")

        # Show failed scenarios
        if failed > 0:
            print(f"\nFailed Scenarios:")
            for r in self.results:
                if not r.get("success", False):
                    error = r.get("error", "Unknown error")
                    print(f"  - {r.get('name', 'Unknown')}: {error}")

        print("=" * 60)

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)


async def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run analysis scenarios")
    parser.add_argument(
        "input",
        help="Path to scenario JSON file or directory containing scenarios",
    )
    parser.add_argument(
        "--output",
        help="Path to save aggregated summary results (optional). Individual reports are always saved to ./reports/",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )

    args = parser.parse_args()

    # Create runner
    runner = ScenarioRunner(verbose=not args.quiet)

    # Determine if input is file or directory
    input_path = Path(args.input)

    if input_path.is_file():
        results = await runner.run_scenarios_from_file(str(input_path))
    elif input_path.is_dir():
        results = await runner.run_all_scenarios(str(input_path))
    else:
        print(f"Error: Invalid input path: {input_path}")
        sys.exit(1)

    # Print summary
    runner.print_summary()

    # Save results
    if args.output:
        runner.save_results(args.output)


if __name__ == "__main__":
    asyncio.run(main())