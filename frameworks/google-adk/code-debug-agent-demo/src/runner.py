"""Runner framework for testing the Code Debug Agent."""

import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from google.adk.runners import InMemoryRunner
from src.agents import get_initial_agent, get_agent_by_name, list_agents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in a debugging conversation."""
    user_input: str
    expected_tools: Optional[List[str]] = None
    expected_keywords: Optional[List[str]] = None
    expected_links: Optional[List[str]] = None


@dataclass
class Scenario:
    """Represents a debugging scenario to test."""
    name: str
    description: str
    error_message: str
    programming_language: Optional[str] = None
    framework: Optional[str] = None
    conversation: List[ConversationTurn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioReport:
    """Report for a single scenario execution."""
    scenario_name: str
    success: bool
    execution_time: float
    tools_used: List[str]
    messages: List[str]
    errors: List[str]
    validation_results: Dict[str, bool]


class ScenarioRunner:
    """Runner for executing debugging scenarios."""

    def __init__(self, agent_name: Optional[str] = None):
        """Initialize the scenario runner.

        Args:
            agent_name: Optional specific agent to use
        """
        self.agent = get_agent_by_name(agent_name) if agent_name else get_initial_agent()
        self.runner = None
        self.session = None

    async def setup(self):
        """Set up the runner and session."""
        self.runner = InMemoryRunner(
            agent=self.agent,
            app_name="code-debug-agent"
        )
        self.session = await self.runner.session_service.create_session(
            app_name=self.runner.app_name,
            user_id="test_user"
        )

    async def run_scenario(self, scenario: Scenario) -> ScenarioReport:
        """Run a single debugging scenario.

        Args:
            scenario: The scenario to execute

        Returns:
            Report of the scenario execution
        """
        logger.info(f"Running scenario: {scenario.name}")
        start_time = datetime.now()

        report = ScenarioReport(
            scenario_name=scenario.name,
            success=True,
            execution_time=0,
            tools_used=[],
            messages=[],
            errors=[],
            validation_results={}
        )

        try:
            # Build the initial error message
            initial_message = scenario.error_message
            if scenario.programming_language:
                initial_message += f"\nLanguage: {scenario.programming_language}"
            if scenario.framework:
                initial_message += f"\nFramework: {scenario.framework}"

            # Execute the conversation
            if scenario.conversation:
                for turn in scenario.conversation:
                    await self._execute_turn(turn, report)
            else:
                # Single turn with just the error message
                turn = ConversationTurn(user_input=initial_message)
                await self._execute_turn(turn, report)

        except Exception as e:
            logger.error(f"Error in scenario {scenario.name}: {e}")
            report.success = False
            report.errors.append(str(e))

        # Calculate execution time
        report.execution_time = (datetime.now() - start_time).total_seconds()
        return report

    async def _execute_turn(self, turn: ConversationTurn, report: ScenarioReport):
        """Execute a single conversation turn.

        Args:
            turn: The conversation turn to execute
            report: Report to update with results
        """
        logger.info(f"User input: {turn.user_input[:100]}...")

        # Import types for creating Content
        from google.genai import types

        # Create a proper Content object with the user input
        content = types.Content(
            parts=[types.Part(text=turn.user_input)],
            role="user"
        )

        # Run the agent
        messages = []
        tools_called = []

        async for event in self.runner.run_async(
            user_id=self.session.user_id,
            session_id=self.session.id,
            new_message=content
        ):
            if hasattr(event, 'content'):
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text'):
                            messages.append(part.text)

            if hasattr(event, 'tool_calls'):
                for tool_call in event.tool_calls:
                    tools_called.append(tool_call.function.name)
                    report.tools_used.append(tool_call.function.name)

        # Store messages
        full_response = "\n".join(messages)
        report.messages.append(full_response)

        # Validate expectations
        if turn.expected_tools:
            tools_match = all(tool in tools_called for tool in turn.expected_tools)
            report.validation_results[f"tools_{len(report.validation_results)}"] = tools_match
            if not tools_match:
                logger.warning(f"Expected tools {turn.expected_tools}, got {tools_called}")

        if turn.expected_keywords:
            keywords_found = all(
                keyword.lower() in full_response.lower()
                for keyword in turn.expected_keywords
            )
            report.validation_results[f"keywords_{len(report.validation_results)}"] = keywords_found
            if not keywords_found:
                logger.warning(f"Missing expected keywords: {turn.expected_keywords}")

        if turn.expected_links:
            links_found = all(
                link in full_response
                for link in turn.expected_links
            )
            report.validation_results[f"links_{len(report.validation_results)}"] = links_found

    async def run_scenarios_from_file(self, file_path: str) -> List[ScenarioReport]:
        """Load and run scenarios from a JSON file.

        Args:
            file_path: Path to the scenarios JSON file

        Returns:
            List of scenario reports
        """
        scenarios = self.load_scenarios(file_path)
        reports = []

        await self.setup()

        for scenario in scenarios:
            report = await self.run_scenario(scenario)
            reports.append(report)
            logger.info(f"Scenario {scenario.name} completed: {'✓' if report.success else '✗'}")

        return reports

    @staticmethod
    def load_scenarios(file_path: str) -> List[Scenario]:
        """Load scenarios from a JSON file.

        Args:
            file_path: Path to the scenarios file

        Returns:
            List of scenarios
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Scenarios file not found: {file_path}")

        with open(path, 'r') as f:
            data = json.load(f)

        scenarios = []
        for item in data.get('scenarios', []):
            conversation = []
            for turn_data in item.get('conversation', []):
                conversation.append(ConversationTurn(
                    user_input=turn_data.get('user_input', turn_data.get('user', '')),
                    expected_tools=turn_data.get('expected_tools'),
                    expected_keywords=turn_data.get('expected_keywords'),
                    expected_links=turn_data.get('expected_links')
                ))

            scenario = Scenario(
                name=item['name'],
                description=item.get('description', ''),
                error_message=item['error_message'],
                programming_language=item.get('programming_language'),
                framework=item.get('framework'),
                conversation=conversation,
                metadata=item.get('metadata', {})
            )
            scenarios.append(scenario)

        return scenarios

    def generate_report(self, reports: List[ScenarioReport]) -> str:
        """Generate a summary report from scenario executions.

        Args:
            reports: List of scenario reports

        Returns:
            Formatted report string
        """
        total = len(reports)
        successful = sum(1 for r in reports if r.success)
        total_time = sum(r.execution_time for r in reports)

        report_lines = [
            "=" * 60,
            "CODE DEBUG AGENT - SCENARIO EXECUTION REPORT",
            "=" * 60,
            f"Total Scenarios: {total}",
            f"Successful: {successful}/{total} ({successful/total*100:.1f}%)",
            f"Total Execution Time: {total_time:.2f}s",
            f"Average Time per Scenario: {total_time/total:.2f}s",
            "",
            "Scenario Results:",
            "-" * 40,
        ]

        for report in reports:
            status = "✓ PASS" if report.success else "✗ FAIL"
            report_lines.append(f"{status} | {report.scenario_name} ({report.execution_time:.2f}s)")

            if report.tools_used:
                report_lines.append(f"     Tools: {', '.join(set(report.tools_used))}")

            if report.errors:
                report_lines.append(f"     Errors: {', '.join(report.errors)}")

            if report.validation_results:
                failed_validations = [
                    k for k, v in report.validation_results.items() if not v
                ]
                if failed_validations:
                    report_lines.append(f"     Failed Validations: {', '.join(failed_validations)}")

        report_lines.append("=" * 60)
        return "\n".join(report_lines)


async def main():
    """Main function to run debugging scenarios."""
    import sys
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list-agents":
            print("Available Agents:")
            for agent_info in list_agents():
                print(f"  - {agent_info['name']}: {agent_info['description'][:50]}...")
                print(f"    Model: {agent_info['model']}")
                print(f"    Tools: {', '.join(agent_info['tools'])}")
            return

        scenario_file = sys.argv[1]
        agent_name = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Default to sample scenarios
        scenario_file = "src/scenarios/sample_errors.json"
        agent_name = None

    # Create runner
    runner = ScenarioRunner(agent_name=agent_name)

    # Check if scenario file exists
    if not Path(scenario_file).exists():
        print(f"Creating sample scenario file: {scenario_file}")
        # Create sample scenarios
        sample_scenarios = {
            "scenarios": [
                {
                    "name": "Python Import Error",
                    "description": "Test handling of Python import errors",
                    "error_message": "ImportError: No module named 'pandas'",
                    "programming_language": "python",
                    "conversation": [
                        {
                            "user_input": "ImportError: No module named 'pandas'",
                            "expected_tools": ["search_stack_exchange_for_error"],
                            "expected_keywords": ["pip install", "pandas"]
                        }
                    ]
                },
                {
                    "name": "JavaScript TypeError",
                    "description": "Test handling of JavaScript type errors",
                    "error_message": "TypeError: Cannot read property 'map' of undefined",
                    "programming_language": "javascript",
                    "framework": "react",
                    "conversation": [
                        {
                            "user_input": "TypeError: Cannot read property 'map' of undefined in React",
                            "expected_tools": ["search_stack_exchange_for_error", "analyze_error_and_suggest_fix"],
                            "expected_keywords": ["undefined", "map", "array"]
                        }
                    ]
                }
            ]
        }

        # Create scenarios directory if it doesn't exist
        Path("src/scenarios").mkdir(parents=True, exist_ok=True)

        with open(scenario_file, 'w') as f:
            json.dump(sample_scenarios, f, indent=2)

    # Run scenarios
    try:
        reports = await runner.run_scenarios_from_file(scenario_file)
        print("\n" + runner.generate_report(reports))
    except Exception as e:
        print(f"Error running scenarios: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())