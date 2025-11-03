"""
Scenario runner for executing and validating test scenarios
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Optional
import argparse

from .context import (
    TestScenarioDefinition,
    ConversationTurn,
    ExecutionResult,
    ScenarioReport,
    AnalysisRequest,
    Config,
)
from .crew import run_unit_test_generation


class ScenarioRunner:
    """Executes test scenarios and validates results"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.config = Config()

    def load_scenario(self, file_path: str) -> TestScenarioDefinition:
        """Load a scenario from a JSON file"""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return TestScenarioDefinition(**data)
        except Exception as e:
            raise ValueError(f"Failed to load scenario from {file_path}: {str(e)}")

    def load_scenarios_from_directory(self, directory: str) -> List[TestScenarioDefinition]:
        """Load all scenario files from a directory"""
        scenarios = []
        scenario_dir = Path(directory)

        if not scenario_dir.exists():
            raise ValueError(f"Scenario directory not found: {directory}")

        for json_file in scenario_dir.glob("*.json"):
            try:
                scenario = self.load_scenario(str(json_file))
                scenarios.append(scenario)
                if self.verbose:
                    print(f"Loaded scenario: {scenario.name}")
            except Exception as e:
                print(f"Warning: Failed to load {json_file}: {str(e)}")

        return scenarios

    def validate_turn(self, turn: ConversationTurn, crew_output: str) -> tuple[bool, List[str]]:
        """
        Validate the crew output against expected outcomes

        Returns:
            Tuple of (validation_passed, list_of_errors)
        """
        errors = []
        expected = turn.expected

        # Convert output to lowercase for case-insensitive matching
        output_lower = crew_output.lower()

        # Check for required message content
        if expected.message_contains:
            for required_text in expected.message_contains:
                if required_text.lower() not in output_lower:
                    errors.append(f"Expected text not found in output: '{required_text}'")

        # Check for test plan creation
        if expected.test_plan_created:
            test_plan_indicators = ["test plan", "test scenario", "test case"]
            if not any(indicator in output_lower for indicator in test_plan_indicators):
                errors.append("Test plan not found in output")

        # Check for test code generation
        if expected.test_code_generated:
            test_code_indicators = ["def test_", "import pytest", "assert"]
            if not any(indicator in output_lower for indicator in test_code_indicators):
                errors.append("Generated test code not found in output")

        # Check for imports
        if expected.contains_imports:
            if "import" not in output_lower:
                errors.append("Import statements not found in output")

        # Check for assertions
        if expected.contains_assertions:
            if "assert" not in output_lower:
                errors.append("Assertions not found in output")

        validation_passed = len(errors) == 0
        return validation_passed, errors

    def execute_turn(
        self, turn: ConversationTurn, turn_number: int, context: AnalysisRequest
    ) -> ExecutionResult:
        """Execute a single conversation turn"""
        start_time = time.time()

        if self.verbose:
            print(f"\n{'=' * 80}")
            print(f"Turn {turn_number}: {turn.user_input}")
            print(f"{'=' * 80}\n")

        try:
            # Run the crew
            result = run_unit_test_generation(
                repository_url=context.repository_url,
                file_path=context.file_path,
                function_name=context.function_name,
                verbose=self.verbose,
            )

            crew_output = result.get("raw_output", "")

            # Validate the output
            validation_passed, validation_errors = self.validate_turn(turn, crew_output)

            execution_time = time.time() - start_time

            if self.verbose:
                print(f"\nValidation: {'PASSED' if validation_passed else 'FAILED'}")
                if validation_errors:
                    print("Validation errors:")
                    for error in validation_errors:
                        print(f"  - {error}")
                print(f"Execution time: {execution_time:.2f}s")

            return ExecutionResult(
                turn_number=turn_number,
                user_input=turn.user_input,
                crew_output=crew_output,
                validation_passed=validation_passed,
                validation_errors=validation_errors,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing turn: {str(e)}"
            if self.verbose:
                print(f"\nERROR: {error_msg}")

            return ExecutionResult(
                turn_number=turn_number,
                user_input=turn.user_input,
                crew_output="",
                validation_passed=False,
                validation_errors=[error_msg],
                execution_time=execution_time,
            )

    def run_scenario(self, scenario: TestScenarioDefinition) -> ScenarioReport:
        """Execute a complete test scenario"""
        start_time = time.time()

        if self.verbose:
            print(f"\n{'#' * 80}")
            print(f"# Running Scenario: {scenario.name}")
            print(f"# {scenario.description}")
            print(f"{'#' * 80}\n")

        turns = []
        context = scenario.initial_context

        for i, turn in enumerate(scenario.conversation, start=1):
            result = self.execute_turn(turn, i, context)
            turns.append(result)

            # Stop if a turn fails and we're not running full scenarios
            if not result.validation_passed and not self.config.RUN_FULL_SCENARIOS:
                if self.verbose:
                    print("\nStopping scenario execution due to failed turn")
                break

        total_time = time.time() - start_time
        success = all(turn.validation_passed for turn in turns)

        # Generate summary
        passed_turns = sum(1 for turn in turns if turn.validation_passed)
        total_turns = len(turns)
        summary = f"Scenario {'PASSED' if success else 'FAILED'}: {passed_turns}/{total_turns} turns passed"

        if self.verbose:
            print(f"\n{'#' * 80}")
            print(f"# {summary}")
            print(f"# Total execution time: {total_time:.2f}s")
            print(f"{'#' * 80}\n")

        return ScenarioReport(
            scenario=scenario,
            turns=turns,
            total_execution_time=total_time,
            success=success,
            summary=summary,
        )

    def save_report(self, report: ScenarioReport, output_path: str):
        """Save scenario report to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        report_dict = report.model_dump()

        with open(output_file, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        if self.verbose:
            print(f"Report saved to: {output_path}")


def main():
    """CLI entry point for running scenarios"""
    parser = argparse.ArgumentParser(description="Run Unit Test Agent scenarios")
    parser.add_argument(
        "scenario_path",
        nargs="?",
        default="src/scenarios",
        help="Path to scenario file or directory (default: src/scenarios)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--output",
        "-o",
        default="reports",
        help="Output directory for reports (default: reports)",
    )

    args = parser.parse_args()

    runner = ScenarioRunner(verbose=args.verbose)

    # Determine if path is file or directory
    path = Path(args.scenario_path)

    if path.is_file():
        # Run single scenario
        scenario = runner.load_scenario(str(path))
        report = runner.run_scenario(scenario)

        # Save report
        report_path = Path(args.output) / f"{scenario.name.replace(' ', '_').lower()}_report.json"
        runner.save_report(report, str(report_path))

        # Exit with appropriate code
        sys.exit(0 if report.success else 1)

    elif path.is_dir():
        # Run all scenarios in directory
        scenarios = runner.load_scenarios_from_directory(str(path))

        if not scenarios:
            print(f"No scenarios found in {path}")
            sys.exit(1)

        print(f"Found {len(scenarios)} scenario(s) to run\n")

        reports = []
        for scenario in scenarios:
            report = runner.run_scenario(scenario)
            reports.append(report)

            # Save individual report
            report_path = (
                Path(args.output) / f"{scenario.name.replace(' ', '_').lower()}_report.json"
            )
            runner.save_report(report, str(report_path))

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for report in reports:
            status = "✓ PASSED" if report.success else "✗ FAILED"
            print(f"{status}: {report.scenario.name} ({report.total_execution_time:.2f}s)")

        passed = sum(1 for r in reports if r.success)
        total = len(reports)
        print(f"\nTotal: {passed}/{total} scenarios passed")
        print("=" * 80)

        # Exit with appropriate code
        sys.exit(0 if all(r.success for r in reports) else 1)

    else:
        print(f"Error: Path not found: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
