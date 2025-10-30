"""
Test runner for executing fact-checking agent scenarios from JSON files.

This module provides functionality to load and execute predefined
conversation scenarios for testing the LLM fact-checking agent system.
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

from google.adk.runners import InMemoryRunner
from google.genai.types import Part, UserContent

from .agents import get_initial_agent, get_agent_by_name, AGENTS

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
    expected_agent: Optional[str] = None
    expected_tools: Optional[List[str]] = None
    expected_message_contains: Optional[List[str]] = None
    expected_verdict: Optional[str] = None  # For fact-checking specific validation
    skip_validation: bool = False


@dataclass
class Scenario:
    """Represents a complete test scenario."""
    name: str
    description: str
    conversation: List[ConversationTurn]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Results from executing a single conversation turn."""
    turn_number: int
    user_input: str
    messages: List[str]
    tools_called: List[str]
    validation_passed: bool
    validation_errors: List[str]
    execution_time_ms: int
    raw_output: Any
    verdict: Optional[str] = None


@dataclass
class ScenarioReport:
    """Complete report for a scenario execution."""
    scenario_name: str
    description: str
    start_time: str
    end_time: str
    total_turns: int
    successful_turns: int
    failed_turns: int
    turns: List[ExecutionResult]
    overall_success: bool
    execution_time_ms: int


class ScenarioRunner:
    """
    Executes test scenarios and validates results using Google ADK.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the scenario runner.

        Args:
            verbose: Whether to print detailed output during execution
        """
        self.verbose = verbose
        self.runner = None
        self.session = None

    def load_scenario(self, file_path: str) -> Scenario:
        """
        Load a test scenario from a JSON file.

        Args:
            file_path: Path to the JSON scenario file

        Returns:
            TestScenario object
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Parse conversation turns
        conversation = []
        for turn in data.get('conversation', []):
            conversation.append(ConversationTurn(
                user_input=turn['user'],
                expected_agent=turn.get('expected', {}).get('agent'),
                expected_tools=turn.get('expected', {}).get('tools_called'),
                expected_message_contains=turn.get('expected', {}).get('message_contains'),
                expected_verdict=turn.get('expected', {}).get('verdict'),
                skip_validation=turn.get('skip_validation', False)
            ))

        return Scenario(
            name=data['name'],
            description=data['description'],
            conversation=conversation,
            metadata=data.get('metadata', {})
        )

    async def execute_turn(
        self,
        user_input: str,
        turn: ConversationTurn,
        turn_number: int
    ) -> ExecutionResult:
        """
        Execute a single conversation turn.

        Args:
            user_input: User's input message (Q&A to fact-check)
            turn: ConversationTurn with expectations
            turn_number: Current turn number

        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()

        if self.verbose:
            print(f"\n🗣️  User Input:\n{user_input[:200]}...")

        # Create user content
        content = UserContent(parts=[Part(text=user_input)])

        # Collect results
        messages = []
        tools_called = []
        verdict = None

        try:
            # Run the agent
            async for event in self.runner.run_async(
                user_id=self.session.user_id,
                session_id=self.session.id,
                new_message=content
            ):
                # Extract message text
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            messages.append(part.text)
                            if self.verbose:
                                print(f"🤖 Agent: {part.text[:200]}...")

                            # Extract verdict if present
                            if "Overall verdict:" in part.text:
                                verdict_line = [line for line in part.text.split('\n')
                                               if "Overall verdict:" in line]
                                if verdict_line:
                                    verdict = verdict_line[0].split("Overall verdict:")[-1].strip()

                # Check for tool calls in metadata
                if hasattr(event, 'metadata') and event.metadata:
                    if 'tools' in event.metadata:
                        for tool in event.metadata['tools']:
                            tools_called.append(tool)
                            if self.verbose:
                                print(f"🔧 Tool Called: {tool}")

        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return ExecutionResult(
                turn_number=turn_number,
                user_input=user_input,
                messages=[f"Error: {str(e)}"],
                tools_called=[],
                validation_passed=False,
                validation_errors=[f"Execution error: {e}"],
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                raw_output=None,
                verdict=None
            )

        # Validate results
        validation_errors = []
        if not turn.skip_validation:
            validation_errors = self.validate_turn(
                turn,
                tools_called,
                messages,
                verdict
            )

        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return ExecutionResult(
            turn_number=turn_number,
            user_input=user_input,
            messages=messages,
            tools_called=tools_called,
            validation_passed=len(validation_errors) == 0,
            validation_errors=validation_errors,
            execution_time_ms=execution_time,
            raw_output=None,
            verdict=verdict
        )

    def validate_turn(
        self,
        turn: ConversationTurn,
        tools_called: List[str],
        messages: List[str],
        verdict: Optional[str]
    ) -> List[str]:
        """
        Validate a turn's results against expectations.

        Returns:
            List of validation errors (empty if all passed)
        """
        errors = []

        # Validate tools called (google_search should be used)
        if turn.expected_tools:
            for expected_tool in turn.expected_tools:
                if expected_tool not in tools_called:
                    errors.append(f"Expected tool '{expected_tool}' not called")

        # Validate message content
        if turn.expected_message_contains:
            all_messages = " ".join(messages).lower()
            for expected_content in turn.expected_message_contains:
                if expected_content.lower() not in all_messages:
                    errors.append(
                        f"Expected message to contain '{expected_content}' but it didn't"
                    )

        # Validate verdict (fact-checking specific)
        if turn.expected_verdict and verdict:
            if turn.expected_verdict.lower() != verdict.lower():
                errors.append(
                    f"Expected verdict '{turn.expected_verdict}', "
                    f"but got '{verdict}'"
                )

        return errors

    async def run_scenario(self, scenario: Scenario) -> ScenarioReport:
        """
        Run a complete test scenario.

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
            print(f"{'='*60}")

        # Initialize runner and session for the scenario
        agent = get_initial_agent()
        self.runner = InMemoryRunner(agent=agent, app_name="llm-fact-check-agent")
        self.session = await self.runner.session_service.create_session(
            app_name=self.runner.app_name,
            user_id="test_user"
        )

        # Execute each turn
        turns = []
        for i, turn in enumerate(scenario.conversation):
            result = await self.execute_turn(
                turn.user_input,
                turn,
                i + 1
            )
            turns.append(result)

            if self.verbose and result.validation_errors:
                print(f"❌ Validation Errors: {result.validation_errors}")

        # Calculate summary statistics
        successful_turns = sum(1 for t in turns if t.validation_passed)
        failed_turns = len(turns) - successful_turns
        overall_success = failed_turns == 0

        end_time = datetime.now()
        total_time = int((end_time - start_time).total_seconds() * 1000)

        report = ScenarioReport(
            scenario_name=scenario.name,
            description=scenario.description,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_turns=len(turns),
            successful_turns=successful_turns,
            failed_turns=failed_turns,
            turns=turns,
            overall_success=overall_success,
            execution_time_ms=total_time
        )

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Scenario Complete: {scenario.name}")
            print(f"Success: {overall_success} ({successful_turns}/{len(turns)} turns passed)")
            print(f"Time: {total_time}ms")
            print(f"{'='*60}")

        return report

    def save_report(self, report: ScenarioReport, output_dir: str = "reports"):
        """
        Save a scenario report to a JSON file.

        Args:
            report: ScenarioReport to save
            output_dir: Directory to save reports in
        """
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/report_{report.scenario_name}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(asdict(report), f, indent=2)

        if self.verbose:
            print(f"Report saved to: {filename}")


async def run_all_scenarios(
    scenario_dir: str = "src/scenarios",
    verbose: bool = False,
    save_reports: bool = True
) -> Tuple[List[ScenarioReport], bool]:
    """
    Run all scenarios in a directory.

    Args:
        scenario_dir: Directory containing scenario JSON files
        verbose: Whether to print detailed output
        save_reports: Whether to save reports to files

    Returns:
        Tuple of (list of reports, overall success)
    """
    runner = ScenarioRunner(verbose=verbose)
    reports = []

    # Find all scenario files
    scenario_files = list(Path(scenario_dir).glob("*.json"))

    if not scenario_files:
        logger.warning(f"No scenario files found in {scenario_dir}")
        return reports, True

    print(f"Found {len(scenario_files)} scenarios to run")

    for scenario_file in scenario_files:
        print(f"\nRunning scenario: {scenario_file.name}")

        try:
            scenario = runner.load_scenario(str(scenario_file))
            report = await runner.run_scenario(scenario)
            reports.append(report)

            if save_reports:
                runner.save_report(report)

        except Exception as e:
            logger.error(f"Failed to run scenario {scenario_file}: {e}")

    # Summary
    total_scenarios = len(reports)
    successful_scenarios = sum(1 for r in reports if r.overall_success)

    print(f"\n{'='*60}")
    print(f"All Scenarios Complete")
    print(f"Total: {total_scenarios}")
    print(f"Successful: {successful_scenarios}")
    print(f"Failed: {total_scenarios - successful_scenarios}")
    print(f"{'='*60}")

    return reports, all(r.overall_success for r in reports)


if __name__ == "__main__":
    # CLI entrypoint supporting single or all scenarios (aligned with other demos)
    import argparse

    parser = argparse.ArgumentParser(
        description='Run fact-checking test scenarios from JSON files'
    )
    parser.add_argument(
        'scenario_file',
        nargs='?',
        help='Path to a specific scenario JSON file (omit to run all scenarios)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output', '-o',
        help='Path to save the execution report (only for single scenario)'
    )

    args = parser.parse_args()

    async def _main():
        if args.scenario_file:
            runner = ScenarioRunner(verbose=args.verbose)
            try:
                scenario = runner.load_scenario(args.scenario_file)
            except Exception as e:
                print(f"Error loading scenario: {e}")
                sys.exit(1)

            try:
                report = await runner.run_scenario(scenario)
            except Exception as e:
                print(f"Error running scenario: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

            # Save report
            if args.output:
                # Save to explicit path
                with open(args.output, 'w') as f:
                    json.dump(asdict(report), f, indent=2)
                if args.verbose:
                    print(f"Report saved to: {args.output}")
            else:
                # Use default reports directory and naming
                runner.save_report(report)

            # Exit with success based on validation
            sys.exit(0 if report.overall_success else 1)
        else:
            # Run all scenarios and save reports
            _, overall_success = await run_all_scenarios(verbose=args.verbose, save_reports=True)
            sys.exit(0 if overall_success else 1)

    asyncio.run(_main())