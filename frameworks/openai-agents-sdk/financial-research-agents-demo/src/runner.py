"""
Test runner for executing financial research scenarios from JSON files.

This module provides functionality to load and execute predefined
research scenarios for testing the multi-agent system.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, asdict

from .manager import FinancialResearchManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScenarioExpectations:
    """Expected outcomes for a scenario."""
    min_search_terms: Optional[int] = None
    required_sections: Optional[List[str]] = None
    verification_should_pass: Optional[bool] = None
    min_report_length: Optional[int] = None
    required_keywords: Optional[List[str]] = None


@dataclass
class TestScenario:
    """Represents a complete test scenario."""
    name: str
    description: str
    query: str
    expectations: ScenarioExpectations
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ScenarioReport:
    """Complete report for a scenario execution."""
    scenario_name: str
    description: str
    query: str
    start_time: str
    end_time: str
    execution_time_ms: int
    search_terms_count: int
    report_length: int
    verification_status: str
    validation_passed: bool
    validation_errors: List[str]
    full_report: str
    follow_up_questions: List[str]
    overall_success: bool


class ScenarioRunner:
    """
    Executes test scenarios and validates results.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the scenario runner.

        Args:
            verbose: Whether to print detailed output during execution
        """
        self.verbose = verbose

    def load_scenario(self, file_path: str) -> TestScenario:
        """
        Load a test scenario from a JSON file.

        Args:
            file_path: Path to the JSON scenario file

        Returns:
            TestScenario object
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Parse expectations
        expectations_data = data.get('expectations', {})
        expectations = ScenarioExpectations(
            min_search_terms=expectations_data.get('min_search_terms'),
            required_sections=expectations_data.get('required_sections'),
            verification_should_pass=expectations_data.get('verification_should_pass'),
            min_report_length=expectations_data.get('min_report_length'),
            required_keywords=expectations_data.get('required_keywords')
        )

        return TestScenario(
            name=data['name'],
            description=data['description'],
            query=data['query'],
            expectations=expectations,
            metadata=data.get('metadata', {})
        )

    async def run_scenario(self, scenario: TestScenario) -> ScenarioReport:
        """
        Execute a complete test scenario.

        Args:
            scenario: TestScenario to execute

        Returns:
            ScenarioReport with complete results
        """
        start_time = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Running Scenario: {scenario.name}")
            print(f"Description: {scenario.description}")
            print(f"Query: {scenario.query}")
            print(f"{'='*60}")

        # Run the research
        manager = FinancialResearchManager(verbose=self.verbose)
        try:
            result = await manager.run(scenario.query)
        except Exception as e:
            logger.error(f"Error running scenario: {e}")
            end_time = datetime.now()
            return ScenarioReport(
                scenario_name=scenario.name,
                description=scenario.description,
                query=scenario.query,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                execution_time_ms=int((end_time - start_time).total_seconds() * 1000),
                search_terms_count=0,
                report_length=0,
                verification_status="ERROR",
                validation_passed=False,
                validation_errors=[f"Execution error: {e}"],
                full_report="",
                follow_up_questions=[],
                overall_success=False
            )

        end_time = datetime.now()

        # Extract results
        context = result['context']
        report = result['report']
        verification = result['verification']
        follow_up_questions = result.get('follow_up_questions', [])

        # Validate results
        validation_errors = self.validate_results(
            scenario.expectations,
            len(context.search_plan),
            report,
            verification['status'],
            follow_up_questions
        )

        # Generate report
        scenario_report = ScenarioReport(
            scenario_name=scenario.name,
            description=scenario.description,
            query=scenario.query,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            execution_time_ms=int((end_time - start_time).total_seconds() * 1000),
            search_terms_count=len(context.search_plan),
            report_length=len(report),
            verification_status=verification['status'],
            validation_passed=len(validation_errors) == 0,
            validation_errors=validation_errors,
            full_report=report,
            follow_up_questions=follow_up_questions,
            overall_success=len(validation_errors) == 0
        )

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Scenario Complete: {scenario.name}")
            print(f"Result: {'✅ PASSED' if scenario_report.overall_success else '❌ FAILED'}")
            print(f"Execution time: {scenario_report.execution_time_ms}ms")
            if validation_errors:
                print(f"\nValidation Errors:")
                for error in validation_errors:
                    print(f"  • {error}")
            print(f"{'='*60}\n")

        return scenario_report

    def validate_results(
        self,
        expectations: ScenarioExpectations,
        search_terms_count: int,
        report: str,
        verification_status: str,
        follow_up_questions: List[str]
    ) -> List[str]:
        """
        Validate scenario results against expectations.

        Returns:
            List of validation errors (empty if all passed)
        """
        errors = []

        # Validate search terms count
        if expectations.min_search_terms:
            if search_terms_count < expectations.min_search_terms:
                errors.append(
                    f"Expected at least {expectations.min_search_terms} search terms, "
                    f"got {search_terms_count}"
                )

        # Validate required sections
        if expectations.required_sections:
            report_lower = report.lower()
            for section in expectations.required_sections:
                if section.lower() not in report_lower:
                    errors.append(f"Required section '{section}' not found in report")

        # Validate verification status
        if expectations.verification_should_pass is not None:
            passed = verification_status == "PASSED"
            if passed != expectations.verification_should_pass:
                expected_status = "PASSED" if expectations.verification_should_pass else "NEEDS REVISION"
                errors.append(
                    f"Expected verification status '{expected_status}', "
                    f"got '{verification_status}'"
                )

        # Validate report length
        if expectations.min_report_length:
            if len(report) < expectations.min_report_length:
                errors.append(
                    f"Expected report length >= {expectations.min_report_length} chars, "
                    f"got {len(report)}"
                )

        # Validate required keywords
        if expectations.required_keywords:
            report_lower = report.lower()
            for keyword in expectations.required_keywords:
                if keyword.lower() not in report_lower:
                    errors.append(f"Required keyword '{keyword}' not found in report")

        return errors

    def save_report(self, report: ScenarioReport, output_path: str):
        """
        Save a scenario report to a JSON file.

        Args:
            report: ScenarioReport to save
            output_path: Path to save the report
        """
        report_dict = asdict(report)

        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)

        if self.verbose:
            print(f"Report saved to: {output_path}")


async def main():
    """
    Main entry point for running scenarios from command line.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Run financial research test scenarios from JSON files'
    )
    parser.add_argument(
        'scenario_file',
        help='Path to the scenario JSON file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output', '-o',
        help='Path to save the execution report'
    )

    args = parser.parse_args()

    # Check API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Usage: uv run --env-file .env python -m src.runner <scenario_file>")
        sys.exit(1)

    # Create runner and load scenario
    runner = ScenarioRunner(verbose=args.verbose)

    try:
        scenario = runner.load_scenario(args.scenario_file)
    except Exception as e:
        print(f"Error loading scenario: {e}")
        sys.exit(1)

    # Run scenario
    try:
        report = await runner.run_scenario(scenario)
    except Exception as e:
        print(f"Error running scenario: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save report if requested
    if args.output:
        runner.save_report(report, args.output)
    else:
        # Default output path
        output_path = f"report_{scenario.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        runner.save_report(report, output_path)

    # Exit with appropriate code
    sys.exit(0 if report.overall_success else 1)


if __name__ == "__main__":
    asyncio.run(main())
