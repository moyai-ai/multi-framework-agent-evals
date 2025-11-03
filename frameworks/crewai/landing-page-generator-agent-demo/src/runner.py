"""
Test runner for executing landing page generation scenarios.

This module provides functionality to load and execute predefined
conversation scenarios for testing the landing page generator crew.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

from .crew import LandingPageCrew
from .agents import get_agent_by_name, list_agents

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    user_input: str
    expected_output_contains: Optional[List[str]] = None
    expected_sections: Optional[List[str]] = None
    skip_validation: bool = False


@dataclass
class Scenario:
    """Represents a complete test scenario."""
    name: str
    description: str
    initial_idea: str
    conversation: List[ConversationTurn]
    expected_final_output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Results from executing a single scenario."""
    scenario_name: str
    user_input: str
    execution_success: bool
    output_file: Optional[str]
    validation_passed: bool
    validation_errors: List[str]
    execution_time_ms: int
    raw_output: Any


@dataclass
class ScenarioReport:
    """Complete report for a scenario execution."""
    scenario_name: str
    description: str
    start_time: str
    end_time: str
    execution_success: bool
    output_file: Optional[str]
    validation_results: Dict[str, Any]
    execution_time_ms: int
    error: Optional[str] = None


class ScenarioRunner:
    """
    Executes test scenarios and validates results using CrewAI.
    """

    def __init__(self, verbose: bool = False, model_name: str = None):
        """
        Initialize the scenario runner.

        Args:
            verbose: Whether to print detailed output during execution
            model_name: The model to use (defaults to environment variable)
        """
        self.verbose = verbose
        self.model_name = model_name or os.getenv('MODEL_NAME', 'gpt-4')
        self.crew = None

    def load_scenario(self, file_path: str) -> Scenario:
        """
        Load a test scenario from a JSON file.

        Args:
            file_path: Path to the scenario JSON file

        Returns:
            Loaded scenario object
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Parse conversation turns
            conversation = []
            for turn_data in data.get('conversation', []):
                turn = ConversationTurn(
                    user_input=turn_data['user_input'],
                    expected_output_contains=turn_data.get('expected_output_contains'),
                    expected_sections=turn_data.get('expected_sections'),
                    skip_validation=turn_data.get('skip_validation', False)
                )
                conversation.append(turn)

            return Scenario(
                name=data['name'],
                description=data['description'],
                initial_idea=data['initial_idea'],
                conversation=conversation,
                expected_final_output=data.get('expected_final_output'),
                metadata=data.get('metadata')
            )
        except Exception as e:
            logger.error(f"Failed to load scenario from {file_path}: {str(e)}")
            raise

    def validate_output(self, output_file: str, scenario: Scenario) -> Tuple[bool, List[str]]:
        """
        Validate the generated output against scenario expectations.

        Args:
            output_file: Path to the generated HTML file
            scenario: The scenario with expected outputs

        Returns:
            Tuple of (validation_passed, list_of_errors)
        """
        errors = []

        try:
            # Read the generated HTML
            with open(output_file, 'r') as f:
                html_content = f.read()

            # Check for expected sections
            if scenario.expected_final_output:
                expected_sections = scenario.expected_final_output.get('sections', [])
                for section in expected_sections:
                    if section.lower() not in html_content.lower():
                        errors.append(f"Missing expected section: {section}")

                # Check for required elements
                required_elements = scenario.expected_final_output.get('required_elements', [])
                for element in required_elements:
                    if element not in html_content:
                        errors.append(f"Missing required element: {element}")

            # Basic HTML validation
            if '<!DOCTYPE html>' not in html_content:
                errors.append("Missing DOCTYPE declaration")

            if '<html' not in html_content:
                errors.append("Missing HTML tag")

            if '<head>' not in html_content:
                errors.append("Missing HEAD tag")

            if '<body>' not in html_content:
                errors.append("Missing BODY tag")

        except Exception as e:
            errors.append(f"Failed to validate output: {str(e)}")

        return len(errors) == 0, errors

    async def execute_scenario(self, scenario: Scenario) -> ExecutionResult:
        """
        Execute a single scenario.

        Args:
            scenario: The scenario to execute

        Returns:
            Execution result with details
        """
        start_time = datetime.now()
        errors = []

        try:
            # Initialize the crew
            self.crew = LandingPageCrew(
                model_name=self.model_name,
                verbose=self.verbose
            )

            # Execute the crew with the initial idea
            if self.verbose:
                print(f"\nExecuting scenario: {scenario.name}")
                print(f"Initial idea: {scenario.initial_idea}")

            result = self.crew.run(scenario.initial_idea)

            # Calculate execution time
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Validate output if successful
            validation_passed = False
            if result.get('success') and result.get('output_file'):
                validation_passed, errors = self.validate_output(
                    result['output_file'],
                    scenario
                )

            return ExecutionResult(
                scenario_name=scenario.name,
                user_input=scenario.initial_idea,
                execution_success=result.get('success', False),
                output_file=result.get('output_file'),
                validation_passed=validation_passed,
                validation_errors=errors,
                execution_time_ms=execution_time,
                raw_output=result
            )

        except Exception as e:
            logger.error(f"Error executing scenario: {str(e)}")
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return ExecutionResult(
                scenario_name=scenario.name,
                user_input=scenario.initial_idea,
                execution_success=False,
                output_file=None,
                validation_passed=False,
                validation_errors=[str(e)],
                execution_time_ms=execution_time,
                raw_output={"error": str(e)}
            )

    async def run_scenario(self, scenario: Scenario) -> ScenarioReport:
        """
        Run a complete scenario and generate a report.

        Args:
            scenario: The scenario to run

        Returns:
            Complete scenario report
        """
        start_time = datetime.now()
        start_time_str = start_time.isoformat()

        try:
            # Execute the scenario
            result = await self.execute_scenario(scenario)

            # Generate report
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)

            return ScenarioReport(
                scenario_name=scenario.name,
                description=scenario.description,
                start_time=start_time_str,
                end_time=end_time.isoformat(),
                execution_success=result.execution_success,
                output_file=result.output_file,
                validation_results={
                    "passed": result.validation_passed,
                    "errors": result.validation_errors
                },
                execution_time_ms=execution_time,
                error=result.validation_errors[0] if result.validation_errors else None
            )

        except Exception as e:
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)

            return ScenarioReport(
                scenario_name=scenario.name,
                description=scenario.description,
                start_time=start_time_str,
                end_time=end_time.isoformat(),
                execution_success=False,
                output_file=None,
                validation_results={"passed": False, "errors": [str(e)]},
                execution_time_ms=execution_time,
                error=str(e)
            )

    def save_report(self, report: ScenarioReport, output_file: str):
        """
        Save a scenario report to a JSON file.

        Args:
            report: The report to save
            output_file: Path to the output file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(asdict(report), f, indent=2)
            logger.info(f"Report saved to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")


def main():
    """Main entry point for the scenario runner."""
    import argparse

    parser = argparse.ArgumentParser(description='Run landing page generation scenarios')
    parser.add_argument('--scenario', type=str, help='Path to scenario JSON file')
    parser.add_argument('--idea', type=str, help='Direct idea input (alternative to scenario file)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--model', type=str, default='gpt-4', help='Model to use')
    parser.add_argument('--report', type=str, help='Path to save the report')

    args = parser.parse_args()

    # Check for required API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    runner = ScenarioRunner(verbose=args.verbose, model_name=args.model)

    if args.idea:
        # Direct execution with an idea
        print(f"Generating landing page for: {args.idea}")
        crew = LandingPageCrew(model_name=args.model, verbose=args.verbose)
        result = crew.run(args.idea)

        if result.get('success'):
            print(f"\nSuccess! Landing page generated: {result['output_file']}")
        else:
            print(f"\nFailed: {result.get('error', 'Unknown error')}")

    elif args.scenario:
        # Execute a scenario file
        try:
            scenario = runner.load_scenario(args.scenario)
            report = asyncio.run(runner.run_scenario(scenario))

            # Save report if requested
            if args.report:
                runner.save_report(report, args.report)

            # Print summary
            print("\n" + "="*50)
            print(f"Scenario: {report.scenario_name}")
            print(f"Success: {report.execution_success}")
            if report.output_file:
                print(f"Output: {report.output_file}")
            print(f"Validation: {'Passed' if report.validation_results['passed'] else 'Failed'}")
            if report.validation_results.get('errors'):
                print("Errors:")
                for error in report.validation_results['errors']:
                    print(f"  - {error}")
            print(f"Execution time: {report.execution_time_ms}ms")
            print("="*50)

        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    else:
        # Interactive mode
        print("Welcome to the Landing Page Generator!")
        print("="*50)
        idea = input("Enter your landing page idea: ")

        if idea.strip():
            crew = LandingPageCrew(model_name=args.model, verbose=args.verbose)
            result = crew.run(idea)

            if result.get('success'):
                print(f"\nSuccess! Landing page generated: {result['output_file']}")
            else:
                print(f"\nFailed: {result.get('error', 'Unknown error')}")
        else:
            print("No idea provided. Exiting.")


if __name__ == "__main__":
    main()