"""
Scenario Runner

Executes research scenarios from JSON files and validates results.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.context import ResearchContext, ResearchType, WorkflowStage
from src.manager import ResearchManager


class ScenarioRunner:
    """Runs research scenarios and evaluates results."""

    def __init__(self, verbose: bool = True):
        """
        Initialize the scenario runner.

        Args:
            verbose: Whether to print detailed output
        """
        self.verbose = verbose
        self.manager = ResearchManager(verbose=verbose)
        self.results: List[Dict[str, Any]] = []

    async def run_scenario(self, scenario: Dict[str, Any], save_individual_report: bool = True) -> Dict[str, Any]:
        """
        Run a single research scenario.

        Args:
            scenario: Scenario configuration dictionary
            save_individual_report: Whether to save individual report for this scenario

        Returns:
            Results dictionary with execution details
        """
        name = scenario.get("name", "Unnamed Scenario")
        description = scenario.get("description", "")
        query = scenario.get("query", "")
        expectations = scenario.get("expectations", {})
        metadata = scenario.get("metadata", {})

        if not query:
            return {
                "name": name,
                "success": False,
                "error": "No query provided in scenario",
            }

        self._log(f"\n{'=' * 60}")
        self._log(f"Running Scenario: {name}")
        self._log(f"Description: {description}")
        self._log(f"Query: {query}")
        self._log(f"{'=' * 60}")

        # Determine research type from metadata or auto-detect
        research_type_str = metadata.get("research_type", "general")
        research_type = ResearchType[research_type_str.upper()]

        # Start timer
        start_time = time.time()

        try:
            # Conduct research
            context = await self.manager.conduct_research(
                query=query,
                research_type=research_type,
                user_requirements=scenario.get("user_requirements", {}),
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Evaluate results against expectations
            evaluation = self._evaluate_results(context, expectations)

            # Compile results
            result = {
                "name": name,
                "success": True,
                "query": query,
                "research_type": research_type.value,
                "execution_time": execution_time,
                "stages_completed": [stage.value for stage in context.previous_stages],
                "final_stage": context.current_stage.value,
                "search_terms_used": len(context.search_results) if context.search_results else 0,
                "total_results_collected": context.total_results_collected,
                "report_length": len(context.full_report) if context.full_report else 0,
                "full_report": context.full_report,  # Include the actual report
                "evaluation": evaluation,
                "errors": context.errors,
                "warnings": context.warnings,
            }

            # Add verification scores if available
            if context.verification_result:
                result["verification"] = {
                    "is_verified": context.verification_result.is_verified,
                    "accuracy_score": context.verification_result.accuracy_score,
                    "completeness_score": context.verification_result.completeness_score,
                    "consistency_score": context.verification_result.consistency_score,
                }

        except Exception as e:
            result = {
                "name": name,
                "success": False,
                "query": query,
                "error": str(e),
                "execution_time": time.time() - start_time,
            }

        self._log(f"\nScenario '{name}' completed in {result['execution_time']:.2f} seconds")
        self._log(f"Success: {result['success']}")

        if result["success"] and "evaluation" in result:
            self._log(f"Evaluation passed: {result['evaluation']['passed']}")
            self._log(f"Score: {result['evaluation']['score']:.2%}")

        # Save individual report if requested
        if save_individual_report and result["success"]:
            self._save_individual_report(name, result)

        return result

    async def run_scenarios_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Run scenarios from a JSON file.

        Args:
            file_path: Path to the JSON file containing scenarios

        Returns:
            List of results for each scenario
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

        # Handle both single scenario and multiple scenarios
        if "scenarios" in data:
            scenarios = data["scenarios"]
        elif "query" in data:
            # Single scenario file
            scenarios = [data]
        else:
            self._log("Error: Invalid scenario file format")
            return []

        self._log(f"Loaded {len(scenarios)} scenario(s) from {file_path}")

        # Run each scenario
        results = []
        for i, scenario in enumerate(scenarios, 1):
            self._log(f"\n[{i}/{len(scenarios)}] ", end="")
            result = await self.run_scenario(scenario)
            results.append(result)
            self.results.append(result)

        return results

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

    def _evaluate_results(
        self, context: ResearchContext, expectations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate research results against expectations.

        Args:
            context: Research context with results
            expectations: Expected outcomes

        Returns:
            Evaluation results with score and details
        """
        checks = []
        score = 0
        max_score = 0

        # Check minimum search terms
        if "min_search_terms" in expectations:
            max_score += 1
            actual = len(context.search_results) if context.search_results else 0
            expected = expectations["min_search_terms"]
            passed = actual >= expected
            if passed:
                score += 1
            checks.append({
                "check": "minimum_search_terms",
                "expected": expected,
                "actual": actual,
                "passed": passed,
            })

        # Check minimum report length
        if "min_report_length" in expectations:
            max_score += 1
            actual = len(context.full_report) if context.full_report else 0
            expected = expectations["min_report_length"]
            passed = actual >= expected
            if passed:
                score += 1
            checks.append({
                "check": "minimum_report_length",
                "expected": expected,
                "actual": actual,
                "passed": passed,
            })

        # Check required sections
        if "required_sections" in expectations:
            max_score += 1
            required = set(expectations["required_sections"])
            actual = {s.get("title", "") for s in context.report_sections}
            missing = required - actual
            passed = len(missing) == 0
            if passed:
                score += 1
            checks.append({
                "check": "required_sections",
                "expected": list(required),
                "actual": list(actual),
                "missing": list(missing),
                "passed": passed,
            })

        # Check verification status
        if "verification_should_pass" in expectations:
            max_score += 1
            expected = expectations["verification_should_pass"]
            actual = context.verification_result.is_verified if context.verification_result else False
            passed = actual == expected
            if passed:
                score += 1
            checks.append({
                "check": "verification_status",
                "expected": expected,
                "actual": actual,
                "passed": passed,
            })

        # Check for required keywords in report
        if "required_keywords" in expectations:
            max_score += 1
            keywords = expectations["required_keywords"]
            report_lower = context.full_report.lower() if context.full_report else ""
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

        # Check workflow completion
        if "should_complete" in expectations:
            max_score += 1
            expected = expectations["should_complete"]
            actual = context.current_stage == WorkflowStage.COMPLETE
            passed = actual == expected
            if passed:
                score += 1
            checks.append({
                "check": "workflow_completion",
                "expected": expected,
                "actual": actual,
                "passed": passed,
            })

        return {
            "passed": score == max_score if max_score > 0 else True,
            "score": score / max_score if max_score > 0 else 1.0,
            "checks": checks,
            "total_checks": len(checks),
            "passed_checks": score,
        }

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
            avg_results = sum(r.get("total_results_collected", 0) for r in self.results if r.get("success")) / successful
            avg_report_length = sum(r.get("report_length", 0) for r in self.results if r.get("success")) / successful

            print(f"\nAverage Metrics (successful scenarios):")
            print(f"  Execution Time: {avg_time:.2f} seconds")
            print(f"  Results Collected: {avg_results:.1f}")
            print(f"  Report Length: {avg_report_length:.0f} characters")

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

        # Create report data (exclude full_report from results for summary)
        report_data = {
            "metadata": {
                "scenario_name": scenario_name,
                "execution_time": datetime.now().isoformat(),
                "query": result.get("query", ""),
                "research_type": result.get("research_type", ""),
                "execution_duration": result.get("execution_time", 0),
            },
            "report": result.get("full_report", ""),
            "evaluation": result.get("evaluation", {}),
            "verification": result.get("verification", {}),
            "metrics": {
                "search_terms_used": result.get("search_terms_used", 0),
                "total_results_collected": result.get("total_results_collected", 0),
                "report_length": result.get("report_length", 0),
                "stages_completed": result.get("stages_completed", []),
                "final_stage": result.get("final_stage", ""),
            },
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        self._log(f"Individual report saved to: {report_path}")

    def save_results(self, output_path: str = "scenario_results.json") -> None:
        """
        Save aggregated results to a JSON file (without full reports).

        Args:
            output_path: Path to save the results file
        """
        # Create a copy of results without the full_report field for summary
        summary_results = []
        for r in self.results:
            summary = {k: v for k, v in r.items() if k != "full_report"}
            summary_results.append(summary)

        output_data = {
            "execution_time": datetime.now().isoformat(),
            "total_scenarios": len(self.results),
            "results": summary_results,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        self._log(f"\nSummary results saved to: {output_path}")

    def _log(self, message: str, end: str = "\n") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message, end=end)


async def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Run research scenarios")
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