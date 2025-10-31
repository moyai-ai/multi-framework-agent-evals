"""
Scenario Runner and Main Execution

Provides the main entry point and scenario execution capabilities.
"""

import os
import sys
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.database import DatabaseManager, init_database
from src.agents import OrchestratorAgent, list_agents, AGENTS
from src.context import context_manager


class ScenarioResult(BaseModel):
    """Result of a scenario execution."""

    scenario_id: str
    name: str
    success: bool
    execution_time_ms: float
    output: Optional[str] = None
    error: Optional[str] = None
    validation_passed: bool = False
    validation_details: Dict[str, Any] = Field(default_factory=dict)


class ScenarioRunner:
    """Runs test scenarios against the relational data agent system."""

    def __init__(self, scenarios_dir: str = "src/scenarios"):
        """
        Initialize the scenario runner.

        Args:
            scenarios_dir: Path to the scenarios directory
        """
        self.scenarios_dir = scenarios_dir
        self.scenarios = self._load_scenarios()
        self.orchestrator = OrchestratorAgent()
        self.results: List[ScenarioResult] = []

    def _load_scenarios(self) -> Dict[str, Any]:
        """Load all scenario JSON files from the scenarios directory."""
        scenarios = {}

        # Get all JSON files in the scenarios directory
        scenario_files = sorted(Path(self.scenarios_dir).glob("*.json"))

        for scenario_file in scenario_files:
            try:
                with open(scenario_file, "r") as f:
                    data = json.load(f)
                    # Extract the scenario from the nested structure
                    if "scenario" in data:
                        scenario_data = data["scenario"]
                    else:
                        scenario_data = data

                    # Use filename without extension as the key
                    scenario_id = scenario_file.stem
                    # Ensure the scenario has an id
                    if "id" not in scenario_data:
                        scenario_data["id"] = scenario_id

                    scenarios[scenario_id] = scenario_data
                    print(f"Loaded scenario: {scenario_id}")
            except Exception as e:
                print(f"Error loading {scenario_file}: {e}")

        return {"scenarios": scenarios}

    async def run_scenario(self, scenario: Dict[str, Any]) -> ScenarioResult:
        """
        Run a single scenario.

        Args:
            scenario: Scenario definition

        Returns:
            ScenarioResult with execution details
        """
        print(f"\n{'='*60}")
        print(f"Running Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Request: {scenario['request']}")
        print(f"{'='*60}")

        start_time = datetime.now(timezone.utc)

        try:
            # Process the request
            result = await self.orchestrator.process_request(
                scenario["request"],
                session_id=f"scenario_{scenario['id']}"
            )

            execution_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            if result["success"]:
                # Validate the result if validation criteria exist
                validation_passed = True
                validation_details = {}

                if "validation" in scenario:
                    validation = scenario["validation"]

                    # Check for expected content
                    if "should_contain" in validation:
                        for expected in validation["should_contain"]:
                            if expected.lower() not in result["output"].lower():
                                validation_passed = False
                                validation_details[f"missing_{expected}"] = "Expected content not found"

                    # Check row count
                    if "row_count" in validation:
                        # Simple check - count occurrences of common row indicators
                        row_indicators = ["row", "record", "|", "\n"]
                        estimated_rows = sum(result["output"].count(ind) for ind in row_indicators) // len(row_indicators)
                        if estimated_rows != validation["row_count"]:
                            validation_details["row_count"] = f"Expected {validation['row_count']}, got ~{estimated_rows}"

                    # Check for insights
                    if validation.get("provides_insights"):
                        insight_keywords = ["analysis", "trend", "pattern", "insight", "finding"]
                        has_insights = any(kw in result["output"].lower() for kw in insight_keywords)
                        if not has_insights:
                            validation_passed = False
                            validation_details["insights"] = "No insights provided"

                print(f"\n✓ Scenario completed successfully")
                print(f"Output preview: {result['output'][:200]}...")

                return ScenarioResult(
                    scenario_id=scenario["id"],
                    name=scenario["name"],
                    success=True,
                    execution_time_ms=execution_time_ms,
                    output=result["output"],
                    validation_passed=validation_passed,
                    validation_details=validation_details
                )
            else:
                # Check if this was an expected error
                if scenario.get("expected_error"):
                    print(f"\n✓ Expected error occurred: {result.get('error')}")
                    return ScenarioResult(
                        scenario_id=scenario["id"],
                        name=scenario["name"],
                        success=True,  # Expected error is a success
                        execution_time_ms=execution_time_ms,
                        error=result.get("error"),
                        validation_passed=True
                    )
                else:
                    print(f"\n✗ Scenario failed: {result.get('error')}")
                    return ScenarioResult(
                        scenario_id=scenario["id"],
                        name=scenario["name"],
                        success=False,
                        execution_time_ms=execution_time_ms,
                        error=result.get("error")
                    )

        except Exception as e:
            execution_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            print(f"\n✗ Scenario crashed: {str(e)}")
            return ScenarioResult(
                scenario_id=scenario["id"],
                name=scenario["name"],
                success=False,
                execution_time_ms=execution_time_ms,
                error=str(e)
            )

    async def run_all_scenarios(self, filter_category: Optional[str] = None):
        """
        Run all scenarios or filtered by category.

        Args:
            filter_category: Optional category to filter scenarios (e.g., "simple_query", "aggregation")
        """
        # Convert dictionary of scenarios to a list
        all_scenarios = []
        for scenario_id, scenario_data in self.scenarios["scenarios"].items():
            # Ensure each scenario has an id field
            if "id" not in scenario_data:
                scenario_data["id"] = scenario_id
            all_scenarios.append(scenario_data)

        scenarios_to_run = all_scenarios

        if filter_category:
            scenarios_to_run = [s for s in scenarios_to_run if s["id"].startswith(filter_category)]

        print(f"\n{'#'*60}")
        print(f"Running {len(scenarios_to_run)} scenarios")
        print(f"{'#'*60}")

        for scenario in scenarios_to_run:
            result = await self.run_scenario(scenario)
            self.results.append(result)

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print a summary of scenario results."""
        print(f"\n{'#'*60}")
        print("SCENARIO EXECUTION SUMMARY")
        print(f"{'#'*60}\n")

        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        validated = sum(1 for r in self.results if r.validation_passed)
        avg_time = sum(r.execution_time_ms for r in self.results) / total if total > 0 else 0

        print(f"Total Scenarios: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Validation Passed: {validated} ({validated/total*100:.1f}%)")
        print(f"Average Execution Time: {avg_time:.2f}ms")

        print("\nDetailed Results:")
        print("-" * 60)
        for result in self.results:
            status = "✓" if result.success else "✗"
            validation = "✓" if result.validation_passed else "✗"
            print(f"{status} {result.name:40s} {result.execution_time_ms:8.2f}ms  Validation: {validation}")
            if result.error:
                print(f"   Error: {result.error[:100]}")
            if result.validation_details:
                print(f"   Validation Issues: {result.validation_details}")

    def save_results(self, output_file: str = "scenario_results.json"):
        """Save results to individual JSON files in reports folder."""
        execution_time = datetime.now(timezone.utc)

        # Create reports directory if it doesn't exist
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Save each scenario result to a separate file
        for result in self.results:
            # Create filename with scenario_id and timestamp
            timestamp_str = execution_time.strftime('%Y%m%d_%H%M%S')
            filename = f"{result.scenario_id}_{timestamp_str}.json"

            # Create individual report structure
            individual_report = {
                "metadata": {
                    "scenario_id": result.scenario_id,
                    "scenario_name": result.name,
                    "execution_time": execution_time.isoformat(),
                    "execution_time_ms": result.execution_time_ms
                },
                "result": {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                },
                "validation": {
                    "validation_passed": result.validation_passed,
                    "validation_details": result.validation_details
                }
            }

            # Write individual file
            output_path = reports_dir / filename
            with open(output_path, "w") as f:
                json.dump(individual_report, f, indent=2)

            print(f"Saved: {output_path}")

        # Also save the combined summary (optional, for backwards compatibility)
        results_dict = {
            "execution_time": execution_time.isoformat(),
            "results": [r.dict() for r in self.results],
            "summary": {
                "total": len(self.results),
                "successful": sum(1 for r in self.results if r.success),
                "validated": sum(1 for r in self.results if r.validation_passed),
            }
        }

        with open(output_file, "w") as f:
            json.dump(results_dict, f, indent=2)

        print(f"\nCombined results also saved to {output_file}")
        print(f"Individual reports saved to {reports_dir}/")


class InteractiveDemo:
    """Interactive demonstration of the relational data agent."""

    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.session_id = f"interactive_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    async def run(self):
        """Run the interactive demo."""
        print("\n" + "="*60)
        print("RELATIONAL DATA AGENT - INTERACTIVE DEMO")
        print("="*60)
        print("\nWelcome to the Relational Data Agent Demo!")
        print("This system uses multiple AI agents to understand and query relational databases.")
        print("\nAvailable commands:")
        print("  - Type your query in natural language")
        print("  - 'schema' - Show database schema")
        print("  - 'examples' - Show example queries")
        print("  - 'quit' or 'exit' - Exit the demo")
        print("\n" + "="*60)

        while True:
            try:
                user_input = input("\n> ").strip()

                if user_input.lower() in ["quit", "exit"]:
                    print("Thank you for using the Relational Data Agent!")
                    break

                elif user_input.lower() == "schema":
                    await self._show_schema()

                elif user_input.lower() == "examples":
                    self._show_examples()

                elif user_input:
                    await self._process_query(user_input)

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

    async def _process_query(self, query: str):
        """Process a user query."""
        print("\nProcessing your request...")
        print("Agents working: ", end="", flush=True)

        # Show progress
        stages = ["Schema Analysis", "Query Building", "Execution", "Analysis", "Reporting"]
        for stage in stages:
            print(f"[{stage}]", end=" ", flush=True)
            await asyncio.sleep(0.5)  # Small delay for visual effect

        print("\n")

        result = await self.orchestrator.process_request(query, self.session_id)

        if result["success"]:
            print("\n" + "="*60)
            print("RESULTS")
            print("="*60)
            print(result["output"])

            if result.get("insights"):
                print("\n" + "="*60)
                print("INSIGHTS")
                print("="*60)
                for insight in result["insights"]:
                    print(f"- {insight['description']}")

        else:
            print(f"\nError: {result.get('error')}")

    async def _show_schema(self):
        """Show the database schema."""
        from src.tools import schema_inspector_tool
        schema = schema_inspector_tool.invoke({})
        print("\n" + schema)

    def _show_examples(self):
        """Show example queries."""
        examples = [
            "Show me the top 5 customers by total purchase amount",
            "What are the most popular products by sales volume?",
            "List all orders from the last month with customer details",
            "Which products are running low on stock?",
            "Show me the revenue trend by month",
            "Find customers who haven't ordered in the last 30 days",
            "What's the average order value by product category?",
            "Show me all pending orders with their total amounts",
        ]

        print("\n" + "="*60)
        print("EXAMPLE QUERIES")
        print("="*60)
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example}")


async def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key.")
        sys.exit(1)

    # Initialize database
    print("Initializing database...")
    db_manager = init_database()

    # Load sample data
    print("Loading sample data...")
    seed_file = Path("src/data/seed_data.sql")
    if seed_file.exists():
        with open(seed_file, "r") as f:
            sql_commands = f.read()
            # Execute commands one by one
            for command in sql_commands.split(";"):
                command = command.strip()
                if command:
                    # Remove comment lines from the command
                    command_lines = [line for line in command.split("\n") if not line.strip().startswith("--")]
                    command = "\n".join(command_lines).strip()

                    if command:
                        try:
                            db_manager.execute_raw_sql(command)
                        except Exception as e:
                            print(f"Warning: {e}")

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "test":
            # Run test scenarios
            runner = ScenarioRunner()
            filter_cat = sys.argv[2] if len(sys.argv) > 2 else None
            await runner.run_all_scenarios(filter_cat)
            runner.save_results()

        elif command == "demo":
            # Run interactive demo
            demo = InteractiveDemo()
            await demo.run()

        elif command == "list-agents" or command == "agents":
            # List all available agents
            print("\n" + "="*60)
            print("AVAILABLE AGENTS")
            print("="*60)
            print("\nThe following agents are available in this system:\n")

            for agent_name, agent_class in AGENTS.items():
                # Create a temporary instance to get the description
                agent_instance = agent_class()
                print(f"  • {agent_instance.name}")
                print(f"    Type: {agent_instance.agent_type}")
                print(f"    Model: {agent_instance.model_name}")
                if agent_instance.tools:
                    tool_names = [tool.name for tool in agent_instance.tools]
                    print(f"    Tools: {', '.join(tool_names)}")
                else:
                    print(f"    Tools: None (coordinates other agents)")
                print()

            print(f"Total agents: {len(AGENTS)}")
            print("="*60)

        else:
            print(f"Unknown command: {command}")
            print("Usage: python runner.py [test|demo|list-agents] [filter_category]")

    else:
        # Default to interactive demo
        demo = InteractiveDemo()
        await demo.run()


if __name__ == "__main__":
    asyncio.run(main())