"""
Test runner for executing agent scenarios from JSON files.

This module provides functionality to load and execute predefined
conversation scenarios for testing the agent system.
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

from agents import (
    Runner,
    MessageOutputItem,
    HandoffOutputItem,
    ToolCallItem,
    ToolCallOutputItem
)

from .agents import get_initial_agent, get_agent_by_name, AGENTS
from .context import AirlineAgentContext, create_test_context, context_diff
from .guardrails import get_guardrail_message


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
    expected_handoffs: Optional[List[str]] = None
    expected_tools: Optional[List[str]] = None
    expected_context_updates: Optional[List[str]] = None
    expected_message_contains: Optional[List[str]] = None
    skip_validation: bool = False


@dataclass
class TestScenario:
    """Represents a complete test scenario."""
    name: str
    description: str
    initial_context: Dict[str, Any]
    conversation: List[ConversationTurn]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Results from executing a single conversation turn."""
    turn_number: int
    user_input: str
    current_agent: str
    messages: List[str]
    handoffs: List[str]
    tools_called: List[str]
    context_updates: Dict[str, Any]
    guardrails_triggered: List[str]
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
    total_turns: int
    successful_turns: int
    failed_turns: int
    turns: List[ExecutionResult]
    overall_success: bool
    execution_time_ms: int


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
        self.current_agent = None
        self.context = None
        self.input_items = []

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

        # Parse conversation turns
        conversation = []
        for turn in data.get('conversation', []):
            conversation.append(ConversationTurn(
                user_input=turn['user'],
                expected_agent=turn.get('expected', {}).get('agent'),
                expected_handoffs=turn.get('expected', {}).get('handoffs'),
                expected_tools=turn.get('expected', {}).get('tools_called'),
                expected_context_updates=turn.get('expected', {}).get('context_updates'),
                expected_message_contains=turn.get('expected', {}).get('message_contains'),
                skip_validation=turn.get('skip_validation', False)
            ))

        return TestScenario(
            name=data['name'],
            description=data['description'],
            initial_context=data.get('initial_context', {}),
            conversation=conversation,
            metadata=data.get('metadata', {})
        )

    async def execute_turn(
        self,
        user_input: str,
        turn: ConversationTurn
    ) -> ExecutionResult:
        """
        Execute a single conversation turn.

        Args:
            user_input: User's input message
            turn: ConversationTurn with expectations

        Returns:
            ExecutionResult with execution details
        """
        start_time = datetime.now()

        # Add user message to input items
        self.input_items.append({"role": "user", "content": user_input})

        if self.verbose:
            print(f"\n🗣️ User: {user_input}")
            print(f"   Current Agent: {self.current_agent.name}")

        # Run the agent
        try:
            result = await Runner.run(
                self.current_agent,
                self.input_items,
                context=self.context
            )
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return ExecutionResult(
                turn_number=len(self.input_items) // 2,
                user_input=user_input,
                current_agent=self.current_agent.name,
                messages=["Error: " + str(e)],
                handoffs=[],
                tools_called=[],
                context_updates={},
                guardrails_triggered=[],
                validation_passed=False,
                validation_errors=[f"Execution error: {e}"],
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                raw_output=None
            )

        # Process results
        messages = []
        handoffs = []
        tools_called = []
        guardrails_triggered = []
        old_context = self.context

        # Extract information from output items
        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                # Extract text from content items for display/validation
                content_text = " ".join(
                    content_item.text for content_item in item.raw_item.content
                    if hasattr(content_item, 'text')
                )
                messages.append(content_text)
                # Add the assistant message using to_input_item() method
                self.input_items.append(item.to_input_item())
                if self.verbose:
                    print(f"🤖 {self.current_agent.name}: {content_text}")

            elif isinstance(item, HandoffOutputItem):
                handoff_str = f"{self.current_agent.name} -> {item.agent.name}"
                handoffs.append(handoff_str)
                self.current_agent = item.agent
                if self.verbose:
                    print(f"🔄 Handoff: {handoff_str}")

            elif isinstance(item, ToolCallItem):
                tool_name = item.raw_item.name
                tools_called.append(tool_name)
                if self.verbose:
                    print(f"🔧 Tool Call: {tool_name}")

            elif isinstance(item, ToolCallOutputItem):
                if self.verbose and item.output:
                    output_str = str(item.output)
                    print(f"   Tool Output: {output_str[:100]}...")

            # TODO: Fix guardrail handling once we determine the correct type
            # elif isinstance(item, GuardrailTripwireOutputItem):
            #     guardrails_triggered.append(item.guardrail_name)
            #     if self.verbose:
            #         print(f"⚠️ Guardrail Triggered: {item.guardrail_name}")

        # Update context if changed
        if hasattr(result, 'context') and result.context:
            self.context = result.context

        # Calculate context changes
        context_updates = {}
        if old_context != self.context:
            context_updates = context_diff(old_context, self.context)

        # Validate results
        validation_errors = []
        if not turn.skip_validation:
            validation_errors = self.validate_turn(
                turn,
                self.current_agent.name,
                handoffs,
                tools_called,
                context_updates,
                messages
            )

        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return ExecutionResult(
            turn_number=len(self.input_items) // 2,
            user_input=user_input,
            current_agent=self.current_agent.name,
            messages=messages,
            handoffs=handoffs,
            tools_called=tools_called,
            context_updates=context_updates,
            guardrails_triggered=guardrails_triggered,
            validation_passed=len(validation_errors) == 0,
            validation_errors=validation_errors,
            execution_time_ms=execution_time,
            raw_output=result
        )

    def validate_turn(
        self,
        turn: ConversationTurn,
        current_agent: str,
        handoffs: List[str],
        tools_called: List[str],
        context_updates: Dict[str, Any],
        messages: List[str]
    ) -> List[str]:
        """
        Validate a turn's results against expectations.

        Returns:
            List of validation errors (empty if all passed)
        """
        errors = []

        # Validate current agent
        if turn.expected_agent:
            if turn.expected_agent.lower() not in current_agent.lower():
                errors.append(
                    f"Expected agent '{turn.expected_agent}', "
                    f"but current agent is '{current_agent}'"
                )

        # Validate handoffs
        if turn.expected_handoffs:
            for expected_handoff in turn.expected_handoffs:
                if not any(expected_handoff in h for h in handoffs):
                    errors.append(f"Expected handoff '{expected_handoff}' not found")

        # Validate tools called
        if turn.expected_tools:
            for expected_tool in turn.expected_tools:
                if expected_tool not in tools_called:
                    errors.append(f"Expected tool '{expected_tool}' not called")

        # Validate context updates
        if turn.expected_context_updates:
            for expected_field in turn.expected_context_updates:
                if expected_field not in context_updates:
                    errors.append(f"Expected context update '{expected_field}' not found")

        # Validate message content
        if turn.expected_message_contains:
            all_messages = " ".join(messages).lower()
            for expected_content in turn.expected_message_contains:
                if expected_content.lower() not in all_messages:
                    errors.append(
                        f"Expected message to contain '{expected_content}' but it didn't"
                    )

        return errors

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
            print(f"{'='*60}")

        # Initialize context and agent
        self.context = create_test_context(**scenario.initial_context)
        self.current_agent = get_initial_agent()
        self.input_items = []

        # Execute each turn
        results = []
        for i, turn in enumerate(scenario.conversation, 1):
            if self.verbose:
                print(f"\n--- Turn {i} ---")

            result = await self.execute_turn(turn.user_input, turn)
            results.append(result)

            if not result.validation_passed and self.verbose:
                print(f"❌ Validation errors:")
                for error in result.validation_errors:
                    print(f"   - {error}")
            elif self.verbose:
                print(f"✅ Validation passed")

        # Generate report
        end_time = datetime.now()
        successful_turns = sum(1 for r in results if r.validation_passed)
        failed_turns = len(results) - successful_turns

        report = ScenarioReport(
            scenario_name=scenario.name,
            description=scenario.description,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_turns=len(results),
            successful_turns=successful_turns,
            failed_turns=failed_turns,
            turns=results,
            overall_success=failed_turns == 0,
            execution_time_ms=int((end_time - start_time).total_seconds() * 1000)
        )

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Scenario Complete: {scenario.name}")
            print(f"Result: {'✅ PASSED' if report.overall_success else '❌ FAILED'}")
            print(f"Successful turns: {successful_turns}/{len(results)}")
            print(f"Execution time: {report.execution_time_ms}ms")
            print(f"{'='*60}\n")

        return report

    def save_report(self, report: ScenarioReport, output_path: str):
        """
        Save a scenario report to a JSON file.

        Args:
            report: ScenarioReport to save
            output_path: Path to save the report
        """
        # Convert report to dict (excluding raw_output to keep file size reasonable)
        report_dict = asdict(report)
        for turn in report_dict['turns']:
            turn.pop('raw_output', None)

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
        description='Run agent test scenarios from JSON files'
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
    parser.add_argument(
        '--api-key',
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )

    args = parser.parse_args()

    # Set API key if provided
    if args.api_key:
        os.environ['OPENAI_API_KEY'] = args.api_key
    elif not os.environ.get('OPENAI_API_KEY'):
        print("Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --api-key")
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