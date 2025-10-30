"""Scenario runner for Hacker News agent testing."""

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from google.adk.runners import InMemoryRunner

from .agents import get_agent_by_name, get_initial_agent, list_agents

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single conversation turn in a scenario."""

    user_input: str
    expected_agent: Optional[str] = None
    expected_tools: Optional[List[str]] = None
    expected_parameters: Optional[Dict[str, Any]] = None
    expected_output: Optional[Dict[str, Any]] = None
    expected_contains: Optional[List[str]] = None


@dataclass
class Scenario:
    """Represents a test scenario."""

    name: str
    description: str
    conversation: List[ConversationTurn]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionResult:
    """Result of executing a conversation turn."""

    turn_index: int
    user_input: str
    agent_response: str
    agent_used: str
    tools_called: List[str]
    success: bool
    error: Optional[str] = None
    execution_time_ms: int = 0


@dataclass
class ScenarioReport:
    """Report of scenario execution."""

    scenario_name: str
    scenario_description: str
    successful_turns: int
    failed_turns: int
    total_turns: int
    turns: List[ExecutionResult]
    overall_success: bool
    execution_time_ms: int
    timestamp: str


class ScenarioRunner:
    """Runs test scenarios against Hacker News agents."""

    def __init__(self, verbose: bool = False):
        """Initialize the scenario runner.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        self.runner = None

    def load_scenario(self, file_path: str) -> Scenario:
        """Load a scenario from a JSON file.

        Args:
            file_path: Path to the scenario JSON file

        Returns:
            Loaded Scenario object
        """
        logger.info(f"Loading scenario from: {file_path}")

        with open(file_path, "r") as f:
            data = json.load(f)

        conversation = []
        for turn_data in data.get("conversation", []):
            expected = turn_data.get("expected", {})
            turn = ConversationTurn(
                user_input=turn_data["user"],
                expected_agent=expected.get("agent"),
                expected_tools=expected.get("tools_called"),
                expected_parameters=expected.get("parameters"),
                expected_output=expected.get("output_structure"),
                expected_contains=expected.get("message_contains")
            )
            conversation.append(turn)

        scenario = Scenario(
            name=data["name"],
            description=data["description"],
            conversation=conversation,
            metadata=data.get("metadata")
        )

        logger.info(f"Loaded scenario '{scenario.name}' with {len(conversation)} turns")
        return scenario

    async def run_scenario(self, scenario: Scenario) -> ScenarioReport:
        """Execute a scenario and generate a report.

        Args:
            scenario: The scenario to execute

        Returns:
            ScenarioReport with execution results
        """
        logger.info(f"Running scenario: {scenario.name}")
        start_time = datetime.now()

        # Initialize the agent runner with the correct app_name
        initial_agent = get_initial_agent()
        self.runner = InMemoryRunner(initial_agent, app_name="agents")

        turns_results = []
        successful = 0
        failed = 0

        for i, turn in enumerate(scenario.conversation):
            logger.info(f"Executing turn {i+1}/{len(scenario.conversation)}")
            result = await self._execute_turn(i, turn, scenario)

            if result.success:
                successful += 1
                logger.info(f"Turn {i+1} succeeded")
            else:
                failed += 1
                logger.warning(f"Turn {i+1} failed: {result.error}")

            turns_results.append(result)

            if self.verbose:
                print(f"\nTurn {i+1}:")
                print(f"  User: {turn.user_input}")
                print(f"  Response: {result.agent_response[:200]}...")
                print(f"  Success: {result.success}")
                if result.error:
                    print(f"  Error: {result.error}")

        end_time = datetime.now()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        report = ScenarioReport(
            scenario_name=scenario.name,
            scenario_description=scenario.description,
            successful_turns=successful,
            failed_turns=failed,
            total_turns=len(scenario.conversation),
            turns=turns_results,
            overall_success=(failed == 0),
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Scenario '{scenario.name}' completed: {successful}/{len(scenario.conversation)} turns succeeded")
        return report

    async def _execute_turn(self, index: int, turn: ConversationTurn, scenario: Scenario) -> ExecutionResult:
        """Execute a single conversation turn.

        Args:
            index: Turn index
            turn: The conversation turn to execute

        Returns:
            ExecutionResult for this turn
        """
        turn_start = datetime.now()

        try:
            # Select appropriate agent if specified
            agent_name = "default"
            if turn.expected_agent:
                agent = get_agent_by_name(turn.expected_agent)
                if agent:
                    agent_name = turn.expected_agent
                else:
                    logger.warning(f"Agent '{turn.expected_agent}' not found, using default")
                    agent = get_initial_agent()
            else:
                agent = get_initial_agent()

            # Create a fresh runner for each turn
            runner = InMemoryRunner(agent, app_name="agents")

            # Import types for creating Content
            from google.genai import types

            # Create unique session for this turn using the session service
            user_id = "test_user"
            session = await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id=user_id
            )

            # Create a proper Content object with the user input
            content = types.Content(
                parts=[types.Part(text=turn.user_input)],
                role="user"
            )

            # Execute the turn with proper parameters
            # We need to collect the async generator output
            response_parts = []
            async for event in runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=content
            ):
                # Collect response events
                # The actual response will be in the events generated
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)
                        elif hasattr(part, 'function_call') and part.function_call:
                            # Record function calls
                            if hasattr(part.function_call, 'name') and part.function_call.name:
                                response_parts.append(f"[Function Call: {part.function_call.name}]")

            # Combine all response parts
            response = " ".join(response_parts) if response_parts else ""

            # Extract tools called (would need to parse from response in real implementation)
            tools_called = self._extract_tools_from_response(response)

            # Validate expectations
            validation_errors = []

            if turn.expected_tools:
                missing_tools = set(turn.expected_tools) - set(tools_called)
                if missing_tools:
                    validation_errors.append(f"Missing tools: {missing_tools}")

            if turn.expected_contains:
                for expected_text in turn.expected_contains:
                    if expected_text.lower() not in response.lower():
                        validation_errors.append(f"Missing expected text: '{expected_text}'")

            if turn.expected_output:
                # Try to parse JSON from response
                try:
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response[json_start:json_end]
                        parsed = json.loads(json_str)
                        # Validate structure
                        for key, expected_type in turn.expected_output.items():
                            if key not in parsed:
                                validation_errors.append(f"Missing output key: '{key}'")
                except json.JSONDecodeError:
                    validation_errors.append("Response does not contain valid JSON")

            turn_end = datetime.now()
            execution_time_ms = int((turn_end - turn_start).total_seconds() * 1000)

            return ExecutionResult(
                turn_index=index,
                user_input=turn.user_input,
                agent_response=response,
                agent_used=agent_name,
                tools_called=tools_called,
                success=len(validation_errors) == 0,
                error="; ".join(validation_errors) if validation_errors else None,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            logger.error(f"Error executing turn: {e}")
            turn_end = datetime.now()
            execution_time_ms = int((turn_end - turn_start).total_seconds() * 1000)

            return ExecutionResult(
                turn_index=index,
                user_input=turn.user_input,
                agent_response="",
                agent_used="error",
                tools_called=[],
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms
            )

    def _extract_tools_from_response(self, response: str) -> List[str]:
        """Extract tool names from agent response.

        Args:
            response: Agent response text

        Returns:
            List of tool names called
        """
        # This is a simplified extraction
        # In production, would parse actual tool calls from response
        tools = []
        tool_names = [
            "search_hacker_news",
            "get_trending_stories",
            "analyze_user",
            "analyze_story_comments"
        ]

        for tool in tool_names:
            if tool in response:
                tools.append(tool)

        return tools

    def save_report(self, report: ScenarioReport, output_dir: str = "reports") -> str:
        """Save scenario report to JSON file.

        Args:
            report: The report to save
            output_dir: Directory to save reports

        Returns:
            Path to the saved report
        """
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report.scenario_name}_{timestamp}.json"
        file_path = os.path.join(output_dir, filename)

        with open(file_path, "w") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"Report saved to: {file_path}")
        return file_path


async def main():
    """Main entry point for the scenario runner."""
    parser = argparse.ArgumentParser(description="Run Hacker News agent test scenarios")
    parser.add_argument(
        "scenario",
        nargs="?",
        help="Path to scenario JSON file or directory"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List available agents"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="reports",
        help="Output directory for reports (default: reports)"
    )

    args = parser.parse_args()

    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not found in environment. Please set it in .env file")
        sys.exit(1)

    # List agents if requested
    if args.list_agents:
        print("\nAvailable Agents:")
        print("-" * 60)
        for agent_info in list_agents():
            print(f"Name: {agent_info['name']}")
            print(f"  Description: {agent_info['description']}")
            print(f"  Model: {agent_info['model']}")
            print(f"  Tools: {agent_info['tools']}")
            print()
        return

    # Run scenarios
    runner = ScenarioRunner(verbose=args.verbose)

    if not args.scenario:
        # Run all scenarios in the scenarios directory
        scenario_dir = Path(__file__).parent / "scenarios"
        scenario_files = list(scenario_dir.glob("*.json"))
    else:
        path = Path(args.scenario)
        if path.is_dir():
            scenario_files = list(path.glob("*.json"))
        else:
            scenario_files = [path]

    if not scenario_files:
        logger.error("No scenario files found")
        sys.exit(1)

    print(f"\nRunning {len(scenario_files)} scenario(s)...")
    print("-" * 60)

    all_reports = []
    for scenario_file in scenario_files:
        try:
            scenario = runner.load_scenario(str(scenario_file))
            report = await runner.run_scenario(scenario)
            runner.save_report(report, args.output)
            all_reports.append(report)

            print(f"\n✓ {scenario.name}: {'PASSED' if report.overall_success else 'FAILED'}")
            print(f"  Successful turns: {report.successful_turns}/{report.total_turns}")
            print(f"  Execution time: {report.execution_time_ms}ms")

        except Exception as e:
            logger.error(f"Error running scenario {scenario_file}: {e}")
            print(f"\n✗ {scenario_file.stem}: ERROR - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in all_reports if r.overall_success)
    print(f"Scenarios passed: {passed}/{len(all_reports)}")
    total_time = sum(r.execution_time_ms for r in all_reports)
    print(f"Total execution time: {total_time}ms")
    print(f"Reports saved to: {args.output}/")


if __name__ == "__main__":
    asyncio.run(main())