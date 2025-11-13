"""Runner framework for testing the Code Debug Agent."""

import json
import asyncio
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Suppress known warnings from dependencies
warnings.filterwarnings("ignore", message="Support for google-cloud-storage < 3.0.0.*", category=FutureWarning)
warnings.filterwarnings("ignore", message="Default value is not supported in function declaration.*", category=Warning)
warnings.filterwarnings("ignore", message=".*@model_validator.*mode='after'.*", category=DeprecationWarning)

from google.adk.runners import InMemoryRunner
from src.agents import get_initial_agent, get_agent_by_name, list_agents
from langfuse import get_client
import os
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_trace_via_api(trace_id: str, name: str, tags: list, metadata: dict, user_id: str = None, session_id: str = None):
    """Update a trace via Langfuse REST API ingestion endpoint.

    Args:
        trace_id: The OpenTelemetry trace ID
        name: New trace name
        tags: List of tags
        metadata: Metadata dict
        user_id: Optional user ID
        session_id: Optional session ID
    """
    try:
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not public_key or not secret_key:
            print("[TRACE] Missing Langfuse credentials")
            return

        # Use the ingestion API to update the trace
        url = f"{host}/api/public/ingestion"

        # Generate a unique event ID for this update
        import uuid
        event_id = str(uuid.uuid4())

        payload = {
            "batch": [{
                "id": event_id,
                "type": "trace-create",
                "timestamp": datetime.now().isoformat() + "Z",
                "body": {
                    "id": trace_id,
                    "name": name,
                    "userId": user_id,
                    "sessionId": session_id,
                    "tags": tags,
                    "metadata": metadata,
                }
            }]
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                url,
                json=payload,
                auth=(public_key, secret_key),
            )

            if response.status_code in [200, 201, 207]:
                print(f"[TRACE] API Response: {response.status_code}")
                print(f"[TRACE] Response body: {response.text[:500]}")
                print(f"[TRACE] Successfully updated trace {trace_id} via API")
                return True
            else:
                print(f"[TRACE] Failed to update trace: {response.status_code}")
                print(f"[TRACE] Response: {response.text[:500]}")
                return False

    except Exception as e:
        print(f"[TRACE] Error updating trace via API: {e}")
        return False


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

    def to_dict(self) -> Dict[str, Any]:
        """Convert the report to a dictionary for JSON serialization."""
        return {
            "scenario_name": self.scenario_name,
            "success": self.success,
            "execution_time": self.execution_time,
            "tools_used": self.tools_used,
            "messages": self.messages,
            "errors": self.errors,
            "validation_results": self.validation_results,
            "timestamp": datetime.now().isoformat()
        }


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
            app_name=self.agent.name
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

        # Get OpenTelemetry trace context and update Langfuse
        langfuse = get_client()
        trace_id = None
        try:
            from opentelemetry import trace as otel_trace
            current_span = otel_trace.get_current_span()
            if current_span and current_span.is_recording():
                # Get the trace ID from OpenTelemetry
                trace_id = format(current_span.get_span_context().trace_id, '032x')
                print(f"[TRACE] OpenTelemetry trace ID: {trace_id}")

                # Use Langfuse's trace() method to create/update the trace with this ID
                langfuse.trace(
                    id=trace_id,
                    name=f"Scenario: {scenario.name}",
                    user_id="test_user",
                    session_id=scenario.name,
                    tags=["scenario-test", "evaluation", self.agent.name, scenario.programming_language or "unknown"],
                    metadata={
                        "scenario_name": scenario.name,
                        "programming_language": scenario.programming_language,
                        "framework": scenario.framework,
                        "agent_name": self.agent.name,
                        "test_type": "scenario_execution",
                    },
                    input={
                        "scenario": scenario.name,
                        "error_message": scenario.error_message,
                        "language": scenario.programming_language,
                    }
                )
                print(f"[TRACE] Created Langfuse trace with ID {trace_id} and name: Scenario: {scenario.name}")
            else:
                print(f"[TRACE] No active OpenTelemetry span found")
        except Exception as e:
            print(f"[TRACE] Could not create trace: {e}")
            import traceback
            traceback.print_exc()

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
                    await self._execute_turn(turn, report, scenario.name)
            else:
                # Single turn with just the error message
                turn = ConversationTurn(user_input=initial_message)
                await self._execute_turn(turn, report, scenario.name)

        except Exception as e:
            logger.error(f"Error in scenario {scenario.name}: {e}")
            report.success = False
            report.errors.append(str(e))

            # Update trace with error
            try:
                langfuse.update_current_trace(
                    metadata={
                        "scenario_failed": True,
                        "error_type": type(e).__name__,
                        "error_details": str(e)[:500],
                    }
                )
            except:
                pass

        # Calculate execution time
        report.execution_time = (datetime.now() - start_time).total_seconds()

        # Update trace with final results using the trace ID
        if trace_id:
            try:
                langfuse.trace(
                    id=trace_id,
                    output={
                        "success": report.success,
                        "tools_used": report.tools_used,
                        "execution_time": report.execution_time,
                    },
                    metadata={
                        "execution_completed": True,
                        "total_tools_used": len(report.tools_used),
                        "validation_results": report.validation_results,
                    }
                )
                print(f"[TRACE] Updated trace {trace_id} with final results")
            except Exception as e:
                print(f"[TRACE] Could not update trace with results: {e}")

        return report

    async def _execute_turn(self, turn: ConversationTurn, report: ScenarioReport, scenario_name: str = "unknown"):
        """Execute a single conversation turn.

        Args:
            turn: The conversation turn to execute
            report: Report to update with results
            scenario_name: Name of the scenario for trace naming
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
        trace_id_captured = None

        async for event in self.runner.run_async(
            user_id=self.session.user_id,
            session_id=self.session.id,
            new_message=content
        ):
            # Capture trace ID on first event and update the trace
            if trace_id_captured is None:
                try:
                    from opentelemetry import trace as otel_trace
                    current_span = otel_trace.get_current_span()
                    if current_span and current_span.is_recording():
                        trace_id_captured = format(current_span.get_span_context().trace_id, '032x')
                        print(f"[TRACE] Captured trace ID: {trace_id_captured}")

                        # Update the trace via REST API
                        update_trace_via_api(
                            trace_id=trace_id_captured,
                            name=f"Scenario: {scenario_name}",
                            tags=["scenario-test", "evaluation", self.agent.name],
                            metadata={
                                "scenario_name": scenario_name,
                                "agent_name": self.agent.name,
                                "framework": "google-adk",
                            },
                            user_id=self.session.user_id,
                            session_id=scenario_name,
                        )
                except Exception as e:
                    print(f"[TRACE] Error updating trace: {e}")
                    import traceback
                    traceback.print_exc()

            if hasattr(event, 'content'):
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text is not None:
                            messages.append(part.text)

            if hasattr(event, 'tool_calls'):
                for tool_call in event.tool_calls:
                    tools_called.append(tool_call.function.name)
                    report.tools_used.append(tool_call.function.name)

        # Store messages (filter out any None values just in case)
        full_response = "\n".join(msg for msg in messages if msg is not None)
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

    async def run_scenarios_from_file(self, file_path: str, output_dir: str = "reports") -> List[ScenarioReport]:
        """Load and run scenarios from a JSON file.

        Args:
            file_path: Path to the scenarios JSON file
            output_dir: Directory to save individual scenario reports (default: "reports")

        Returns:
            List of scenario reports
        """
        scenarios = self.load_scenarios(file_path)
        reports = []

        # Create output directory if it doesn't exist
        reports_path = Path(output_dir)
        reports_path.mkdir(parents=True, exist_ok=True)

        await self.setup()

        try:
            for scenario in scenarios:
                report = await self.run_scenario(scenario)
                reports.append(report)
                logger.info(f"Scenario {scenario.name} completed: {'✓' if report.success else '✗'}")

                # Save individual scenario report as JSON
                self.save_scenario_report(report, output_dir)
        finally:
            # Cleanup: give time for any pending async cleanup
            await asyncio.sleep(0.1)

        return reports

    @staticmethod
    def save_scenario_report(report: ScenarioReport, output_dir: str = "reports"):
        """Save a scenario report to a JSON file.

        Args:
            report: The scenario report to save
            output_dir: Directory to save the report (default: "reports")
        """
        reports_path = Path(output_dir)
        reports_path.mkdir(parents=True, exist_ok=True)

        # Create a safe filename from the scenario name
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in report.scenario_name)
        safe_name = safe_name.replace(' ', '_').lower()

        # Add timestamp to make filename unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"

        filepath = reports_path / filename

        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        logger.info(f"Saved scenario report to {filepath}")

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

        # Handle both formats: single scenario (root object) or multiple scenarios (array under 'scenarios' key)
        scenario_items = []
        if 'scenarios' in data:
            # Format with 'scenarios' wrapper containing an array
            scenario_items = data['scenarios']
        elif isinstance(data, list):
            # Format with array at root level
            scenario_items = data
        else:
            # Format with single scenario at root level
            scenario_items = [data]

        for item in scenario_items:
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

        if total == 0:
            return "\n".join([
                "=" * 60,
                "CODE DEBUG AGENT - SCENARIO EXECUTION REPORT",
                "=" * 60,
                "No scenarios were executed.",
                "=" * 60,
            ])

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
                # Format errors more cleanly - extract just the main error message
                error_summaries = []
                for error in report.errors:
                    # Try to extract just the main message from the error
                    if isinstance(error, str):
                        # If it's a quota/rate limit error, extract the key info
                        if "RESOURCE_EXHAUSTED" in error or "429" in error:
                            if "quota" in error.lower():
                                error_summaries.append("Quota exceeded (rate limit)")
                            else:
                                error_summaries.append("Rate limit exceeded")
                        else:
                            # For other errors, show first 100 chars
                            error_summaries.append(error[:100] + "..." if len(error) > 100 else error)
                    else:
                        error_summaries.append(str(error)[:100])

                report_lines.append(f"     Errors: {', '.join(error_summaries)}")

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

        if sys.argv[1] == "--all-scenarios" or sys.argv[1] == "--all":
            # Run all scenario files in the scenarios directory
            scenarios_dir = Path("src/scenarios")
            scenario_files = sorted(scenarios_dir.glob("*.json"))

            if not scenario_files:
                print(f"No scenario files found in {scenarios_dir}")
                return

            agent_name = sys.argv[2] if len(sys.argv) > 2 else None

            print(f"Found {len(scenario_files)} scenario file(s):")
            for file in scenario_files:
                print(f"  - {file.name}")
            print()

            # Run all scenario files
            all_reports = []
            for scenario_file in scenario_files:
                print(f"\n{'='*60}")
                print(f"Running scenarios from: {scenario_file.name}")
                print(f"{'='*60}\n")

                runner = ScenarioRunner(agent_name=agent_name)
                try:
                    reports = await runner.run_scenarios_from_file(str(scenario_file))
                    all_reports.extend(reports)
                except Exception as e:
                    print(f"Error running scenarios from {scenario_file.name}: {e}")

            # Generate combined report
            if all_reports:
                print("\n" + ScenarioRunner(agent_name=agent_name).generate_report(all_reports))

            # Give time for async cleanup
            await asyncio.sleep(0.2)
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
    finally:
        # Give time for async cleanup
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    asyncio.run(main())