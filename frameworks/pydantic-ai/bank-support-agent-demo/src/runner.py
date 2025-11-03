"""Scenario runner for testing bank support agents."""

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .agents import get_agent_by_name, get_initial_agent, get_agent_for_request_type
from .context import (
    BankSupportContext,
    create_initial_context,
    context_diff,
    validate_customer_authentication,
)


console = Console()


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling datetime and Decimal."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    user_input: str
    expected_agent: Optional[str] = None
    expected_tools: Optional[List[str]] = None
    expected_context_updates: Optional[List[str]] = None
    expected_message_contains: Optional[List[str]] = None
    expected_authentication: Optional[bool] = None
    skip_validation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestScenario:
    """Represents a complete test scenario."""
    name: str
    description: str
    initial_context: Dict[str, Any]
    conversation: List[ConversationTurn]
    expected_outcomes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TurnResult:
    """Result from executing a conversation turn."""
    user_input: str
    agent_response: str
    tools_called: List[str]
    context_before: BankSupportContext
    context_after: BankSupportContext
    context_changes: Dict[str, Any]
    execution_time: float
    errors: List[str]


@dataclass
class ScenarioReport:
    """Report from executing a scenario."""
    scenario_name: str
    success: bool
    turn_results: List[TurnResult]
    total_time: float
    errors: List[str]
    summary: Dict[str, Any]


class ScenarioRunner:
    """Executes test scenarios and validates results."""

    def __init__(self, verbose: bool = False, api_key: str = None, reports_dir: str = "reports"):
        self.verbose = verbose
        self.api_key = api_key
        self.reports_dir = Path(reports_dir)
        load_dotenv()

        # Override API key if provided
        if api_key:
            import os
            os.environ["OPENAI_API_KEY"] = api_key

        # Create reports directory if it doesn't exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def run_scenario(self, scenario_path: str) -> ScenarioReport:
        """Execute a scenario from JSON file."""
        scenario_file = Path(scenario_path)
        if not scenario_file.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

        with open(scenario_file) as f:
            data = json.load(f)

        scenario = self._parse_scenario(data)

        if self.verbose:
            console.print(Panel(
                f"[bold blue]Running Scenario: {scenario.name}[/bold blue]\n"
                f"{scenario.description}",
                title="Scenario",
                expand=False
            ))

        return await self._execute_scenario(scenario)

    def _parse_scenario(self, data: Dict[str, Any]) -> TestScenario:
        """Parse scenario data from JSON."""
        # Handle both nested and flat JSON structures
        if "scenario" in data:
            scenario_data = data["scenario"]
        else:
            scenario_data = data

        # Parse conversation turns
        conversation = []
        for turn_data in scenario_data.get("conversation", []):
            if isinstance(turn_data, dict):
                user_input = turn_data.get("user", turn_data.get("user_input", ""))
                expected = turn_data.get("expected", {})

                turn = ConversationTurn(
                    user_input=user_input,
                    expected_agent=expected.get("agent"),
                    expected_tools=expected.get("tools_called", expected.get("tools", [])),
                    expected_context_updates=expected.get("context_updates", []),
                    expected_message_contains=expected.get("message_contains", []),
                    expected_authentication=expected.get("authenticated"),
                    skip_validation=turn_data.get("skip_validation", False),
                    metadata=turn_data.get("metadata", {})
                )
                conversation.append(turn)

        return TestScenario(
            name=scenario_data.get("name", "Unnamed Scenario"),
            description=scenario_data.get("description", ""),
            initial_context=scenario_data.get("initial_context", {}),
            conversation=conversation,
            expected_outcomes=scenario_data.get("expected_outcomes"),
            metadata=scenario_data.get("metadata", data.get("test_configuration", {}))
        )

    async def _execute_scenario(self, scenario: TestScenario) -> ScenarioReport:
        """Execute scenario turns and validate."""
        start_time = time.time()
        turn_results = []
        scenario_errors = []

        # Create initial context
        context = create_initial_context(**scenario.initial_context)

        # Execute each turn
        for i, turn in enumerate(scenario.conversation, 1):
            if self.verbose:
                console.print(f"\n[bold yellow]Turn {i}:[/bold yellow] {turn.user_input}")

            # Create fresh agent for each turn to avoid threading issues
            # Check if we need a specialized agent based on context
            if context.needs_escalation and "fraud" in turn.user_input.lower():
                agent = get_agent_by_name("fraud_specialist")
            elif i == 1 and scenario.metadata and "initial_agent" in scenario.metadata:
                agent = get_agent_by_name(scenario.metadata["initial_agent"])
            else:
                agent = get_initial_agent()

            # Check if agent initialization failed
            if agent is None:
                scenario_errors.append("Could not initialize agent")
                turn_result = TurnResult(
                    user_input=turn.user_input,
                    agent_response="Error: Could not initialize agent",
                    tools_called=[],
                    context_before=context,
                    context_after=context,
                    context_changes={},
                    execution_time=0,
                    errors=["Could not initialize agent"]
                )
                turn_results.append(turn_result)
                continue

            turn_result = await self._execute_turn(agent, context, turn, i)
            turn_results.append(turn_result)

            if turn_result.errors and not turn.skip_validation:
                scenario_errors.extend(turn_result.errors)

            # Update context for next turn (create a copy to avoid issues)
            context = turn_result.context_after.model_copy(deep=True)

        # Generate summary
        total_time = time.time() - start_time
        summary = self._generate_summary(scenario, turn_results)

        success = len(scenario_errors) == 0

        if self.verbose:
            self._print_summary(summary, success, total_time)

        report = ScenarioReport(
            scenario_name=scenario.name,
            success=success,
            turn_results=turn_results,
            total_time=total_time,
            errors=scenario_errors,
            summary=summary
        )

        # Save JSON report
        self._save_json_report(report, scenario.name)

        return report

    async def _execute_turn(
        self,
        agent,
        context: BankSupportContext,
        turn: ConversationTurn,
        turn_number: int
    ) -> TurnResult:
        """Execute a single conversation turn."""
        turn_start = time.time()
        errors = []
        tools_called = []
        context_before = context.model_copy(deep=True)

        try:
            # Run the agent
            result = await agent.run(
                turn.user_input,
                deps=context
            )

            # Extract response and tool calls
            # Pydantic AI uses result.output for the response
            agent_response = result.output if hasattr(result, 'output') else str(result)

            # Track tool calls from the messages
            tools_called = []
            try:
                # Get all messages from this run to check for tool calls
                if hasattr(result, 'all_messages'):
                    messages = result.all_messages()
                    for msg in messages:
                        # Check if message contains tool call information
                        if hasattr(msg, 'parts'):
                            for part in msg.parts:
                                if hasattr(part, 'tool_name'):
                                    tools_called.append(part.tool_name)
            except:
                pass  # If we can't get tool calls, continue without them

            # The context is modified in place during tool execution
            context_after = context

            # Calculate context changes
            context_changes = context_diff(context_before, context_after)

            # Validate the turn if not skipped
            if not turn.skip_validation:
                validation_errors = self._validate_turn(turn, {
                    "response": agent_response,
                    "tools_called": tools_called,
                    "context": context_after,
                    "context_changes": context_changes
                })
                errors.extend(validation_errors)

            if self.verbose:
                console.print(f"[green]Response:[/green] {agent_response[:200]}...")
                if tools_called:
                    console.print(f"[cyan]Tools used:[/cyan] {', '.join(tools_called)}")

        except Exception as e:
            agent_response = f"Error: {str(e)}"
            context_after = context
            context_changes = {}
            errors.append(f"Turn {turn_number} execution failed: {str(e)}")

            if self.verbose:
                console.print(f"[red]Error:[/red] {str(e)}")

        return TurnResult(
            user_input=turn.user_input,
            agent_response=agent_response,
            tools_called=tools_called,
            context_before=context_before,
            context_after=context_after,
            context_changes=context_changes,
            execution_time=time.time() - turn_start,
            errors=errors
        )

    def _validate_turn(self, turn: ConversationTurn, result: Dict[str, Any]) -> List[str]:
        """Validate a turn's output against expectations."""
        errors = []

        # Check expected agent
        if turn.expected_agent:
            # Agent validation would go here if we track active agent
            pass

        # Check expected tools
        if turn.expected_tools:
            tools_called = result.get("tools_called", [])
            for expected_tool in turn.expected_tools:
                if expected_tool not in tools_called:
                    errors.append(f"Expected tool '{expected_tool}' was not called")

        # Check context updates
        if turn.expected_context_updates:
            context_changes = result.get("context_changes", {})
            for expected_field in turn.expected_context_updates:
                if expected_field not in context_changes:
                    errors.append(f"Expected context field '{expected_field}' was not updated")

        # Check message contents
        if turn.expected_message_contains:
            response = result.get("response", "").lower()
            for expected_text in turn.expected_message_contains:
                if expected_text.lower() not in response:
                    errors.append(f"Response did not contain expected text: '{expected_text}'")

        # Check authentication status
        if turn.expected_authentication is not None:
            context = result.get("context")
            if context and context.authenticated != turn.expected_authentication:
                errors.append(
                    f"Expected authentication status to be {turn.expected_authentication}, "
                    f"but got {context.authenticated}"
                )

        return errors

    def _scenario_report_to_dict(self, report: ScenarioReport) -> Dict[str, Any]:
        """Convert ScenarioReport to JSON-serializable dictionary."""
        return {
            "scenario_name": report.scenario_name,
            "success": report.success,
            "total_time": report.total_time,
            "errors": report.errors,
            "summary": report.summary,
            "timestamp": datetime.now().isoformat(),
            "turn_results": [
                {
                    "user_input": tr.user_input,
                    "agent_response": tr.agent_response,
                    "tools_called": tr.tools_called,
                    "context_before": tr.context_before.model_dump(mode="json") if tr.context_before else None,
                    "context_after": tr.context_after.model_dump(mode="json") if tr.context_after else None,
                    "context_changes": tr.context_changes,
                    "execution_time": tr.execution_time,
                    "errors": tr.errors
                }
                for tr in report.turn_results
            ]
        }

    def _save_json_report(self, report: ScenarioReport, scenario_identifier: str):
        """Save scenario report as JSON file."""
        # Create a safe filename from scenario identifier
        safe_name = re.sub(r'[^\w\s-]', '', scenario_identifier).strip()
        safe_name = re.sub(r'[-\s]+', '_', safe_name).lower()
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = self.reports_dir / f"{safe_name}_{timestamp}.json"
        
        report_dict = self._scenario_report_to_dict(report)
        
        with open(report_filename, 'w') as f:
            json.dump(report_dict, f, indent=2, cls=JSONEncoder)
        
        if self.verbose:
            console.print(f"[dim]Report saved to: {report_filename}[/dim]")

    def _generate_summary(self, scenario: TestScenario, turn_results: List[TurnResult]) -> Dict[str, Any]:
        """Generate summary statistics for the scenario."""
        total_tools_called = sum(len(tr.tools_called) for tr in turn_results)
        total_errors = sum(len(tr.errors) for tr in turn_results)
        avg_turn_time = sum(tr.execution_time for tr in turn_results) / len(turn_results) if turn_results else 0

        # Check final authentication status
        final_authenticated = False
        if turn_results:
            final_context = turn_results[-1].context_after
            final_authenticated = validate_customer_authentication(final_context)

        return {
            "total_turns": len(turn_results),
            "total_tools_called": total_tools_called,
            "total_errors": total_errors,
            "average_turn_time": round(avg_turn_time, 3),
            "final_authenticated": final_authenticated,
            "successful_turns": len([tr for tr in turn_results if not tr.errors]),
            "failed_turns": len([tr for tr in turn_results if tr.errors]),
        }

    def _print_summary(self, summary: Dict[str, Any], success: bool, total_time: float):
        """Print formatted summary to console."""
        table = Table(title="Scenario Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        for key, value in summary.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        table.add_row("Total Time", f"{total_time:.2f}s")
        table.add_row("Status", "[green]PASSED[/green]" if success else "[red]FAILED[/red]")

        console.print(table)

    async def run_all_scenarios(self, scenario_dir: str) -> Dict[str, ScenarioReport]:
        """Run all scenarios in a directory."""
        scenario_path = Path(scenario_dir)
        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenario directory not found: {scenario_dir}")

        reports = {}
        scenario_files = list(scenario_path.glob("*.json"))

        if not scenario_files:
            console.print(f"[yellow]No scenario files found in {scenario_dir}[/yellow]")
            return reports

        console.print(f"[bold]Running {len(scenario_files)} scenarios...[/bold]\n")

        for scenario_file in scenario_files:
            try:
                report = await self.run_scenario(str(scenario_file))
                reports[scenario_file.stem] = report
            except Exception as e:
                console.print(f"[red]Failed to run {scenario_file.name}: {str(e)}[/red]")
                error_report = ScenarioReport(
                    scenario_name=scenario_file.stem,
                    success=False,
                    turn_results=[],
                    total_time=0,
                    errors=[str(e)],
                    summary={}
                )
                reports[scenario_file.stem] = error_report
                # Save error report as well
                self._save_json_report(error_report, scenario_file.stem)

        # Print overall summary
        self._print_overall_summary(reports)

        return reports

    def _print_overall_summary(self, reports: Dict[str, ScenarioReport]):
        """Print overall summary of all scenarios."""
        passed = sum(1 for r in reports.values() if r.success)
        failed = len(reports) - passed
        total_time = sum(r.total_time for r in reports.values())

        table = Table(title="Overall Results")
        table.add_column("Scenario", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Time (s)", style="yellow")
        table.add_column("Errors", style="red")

        for name, report in reports.items():
            status = "[green]PASSED[/green]" if report.success else "[red]FAILED[/red]"
            table.add_row(
                name,
                status,
                f"{report.total_time:.2f}",
                str(len(report.errors))
            )

        console.print(table)

        console.print(
            Panel(
                f"[bold]Total Scenarios:[/bold] {len(reports)}\n"
                f"[green]Passed:[/green] {passed}\n"
                f"[red]Failed:[/red] {failed}\n"
                f"[yellow]Total Time:[/yellow] {total_time:.2f}s",
                title="Summary",
                expand=False
            )
        )


async def main():
    """Main entry point for running scenarios."""
    import argparse

    parser = argparse.ArgumentParser(description="Run bank support agent scenarios")
    parser.add_argument("scenario", help="Scenario file or directory to run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--api-key", help="OpenAI API key")

    args = parser.parse_args()

    runner = ScenarioRunner(verbose=args.verbose, api_key=args.api_key)

    scenario_path = Path(args.scenario)

    if scenario_path.is_file():
        # Run single scenario
        report = await runner.run_scenario(str(scenario_path))
        if not report.success:
            exit(1)
    elif scenario_path.is_dir():
        # Run all scenarios in directory
        reports = await runner.run_all_scenarios(str(scenario_path))
        if any(not r.success for r in reports.values()):
            exit(1)
    else:
        console.print(f"[red]Invalid path: {scenario_path}[/red]")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())