"""Main runner for the Meta Quest Knowledge Agent demo."""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

from src.agents import list_agents
from src.crew import create_crew


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Runs test scenarios for the Meta Quest knowledge agent."""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "./results/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.crew = create_crew()

    def load_scenario(self, scenario_path: str) -> Dict[str, Any]:
        """Load a scenario from a JSON file."""
        try:
            with open(scenario_path, "r") as f:
                scenario = json.load(f)
            logger.info(f"Loaded scenario: {scenario.get('name', 'Unnamed')}")
            return scenario
        except Exception as e:
            logger.error(f"Error loading scenario from {scenario_path}: {e}")
            raise

    def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single scenario.

        Args:
            scenario: The scenario configuration

        Returns:
            Results of running the scenario
        """
        scenario_name = scenario.get("name", "Unnamed Scenario")
        logger.info(f"Running scenario: {scenario_name}")

        results = {
            "scenario_name": scenario_name,
            "description": scenario.get("description", ""),
            "timestamp": datetime.now().isoformat(),
            "turns": [],
            "success": True,
            "errors": [],
        }

        # Get conversation turns
        conversation = scenario.get("conversation", [])

        try:
            # Run conversation
            for i, turn in enumerate(conversation):
                user_input = turn.get("user", "")
                if not user_input:
                    continue

                logger.info(f"Turn {i+1}: {user_input}")

                # Get response from crew
                try:
                    response = self.crew.answer_question(user_input)

                    turn_result = {
                        "turn_number": i + 1,
                        "user": user_input,
                        "assistant": response,
                        "validation": self._validate_turn(turn, response),
                    }

                    results["turns"].append(turn_result)

                    # Check validation
                    if not turn_result["validation"]["passed"]:
                        results["success"] = False

                except Exception as e:
                    error_msg = f"Error in turn {i+1}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["success"] = False

        except Exception as e:
            error_msg = f"Error running scenario: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            results["success"] = False

        return results

    def _validate_turn(self, turn: Dict[str, Any], response: str) -> Dict[str, Any]:
        """
        Validate a conversation turn.

        Args:
            turn: The turn configuration with expected outputs
            response: The actual response from the agent

        Returns:
            Validation results
        """
        validation = {
            "passed": True,
            "checks": [],
        }

        expected = turn.get("expected", {})

        # Check if response contains expected keywords
        if "message_contains" in expected:
            for keyword in expected["message_contains"]:
                contains = keyword.lower() in response.lower()
                validation["checks"].append({
                    "check": f"Contains '{keyword}'",
                    "passed": contains,
                })
                if not contains:
                    validation["passed"] = False

        # Check if response contains expected output
        if "expected_output_contains" in expected:
            for keyword in expected["expected_output_contains"]:
                contains = keyword.lower() in response.lower()
                validation["checks"].append({
                    "check": f"Output contains '{keyword}'",
                    "passed": contains,
                })
                if not contains:
                    validation["passed"] = False

        # Skip validation if flag is set
        if turn.get("skip_validation", False):
            validation["passed"] = True
            validation["checks"].append({
                "check": "Validation skipped",
                "passed": True,
            })

        return validation

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save scenario results to a file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}.json"

        output_path = self.output_dir / filename

        try:
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_results_summary(self, results: Dict[str, Any]):
        """Print a summary of the results."""
        print("\n" + "=" * 80)
        print(f"Scenario: {results['scenario_name']}")
        print(f"Status: {'✓ PASSED' if results['success'] else '✗ FAILED'}")
        print(f"Turns: {len(results['turns'])}")

        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")

        print("=" * 80)

        # Print each turn
        for turn in results['turns']:
            print(f"\nTurn {turn['turn_number']}:")
            print(f"User: {turn['user']}")
            print(f"Assistant: {turn['assistant'][:200]}..." if len(turn['assistant']) > 200 else f"Assistant: {turn['assistant']}")

            validation = turn['validation']
            if validation['checks']:
                print(f"Validation: {'✓' if validation['passed'] else '✗'}")
                for check in validation['checks']:
                    status = "✓" if check['passed'] else "✗"
                    print(f"  {status} {check['check']}")

        print("\n" + "=" * 80 + "\n")


def list_available_agents():
    """List all available agents."""
    agents = list_agents()

    print("\nAvailable Meta Quest Knowledge Agents:")
    print("=" * 80)

    for agent in agents:
        print(f"\nName: {agent['name']}")
        print(f"Role: {agent['role']}")
        print(f"Goal: {agent['goal']}")
        if agent['tools']:
            print(f"Tools: {', '.join(agent['tools'])}")

    print("\n" + "=" * 80 + "\n")


def run_interactive_mode():
    """Run in interactive mode for testing questions."""
    print("\n" + "=" * 80)
    print("Meta Quest Knowledge Agent - Interactive Mode")
    print("=" * 80)
    print("Ask questions about Meta Quest. Type 'quit' or 'exit' to stop.\n")

    crew = create_crew()

    while True:
        try:
            question = input("You: ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if not question:
                continue

            print("\nAgent: ", end="", flush=True)
            response = crew.answer_question(question)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Main entry point for the runner."""
    parser = argparse.ArgumentParser(
        description="Meta Quest Knowledge Agent Demo Runner"
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        help="Path to scenario JSON file(s)",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available agents",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save results",
    )

    args = parser.parse_args()

    # Set verbose mode
    if args.verbose:
        os.environ["CREW_VERBOSE"] = "true"
        logging.getLogger().setLevel(logging.DEBUG)

    # List agents
    if args.list_agents:
        list_available_agents()
        return

    # Interactive mode
    if args.interactive:
        run_interactive_mode()
        return

    # Run scenario(s)
    if args.scenario:
        runner = ScenarioRunner(output_dir=args.output_dir)

        # Load and run scenario
        scenario = runner.load_scenario(args.scenario)
        results = runner.run_scenario(scenario)

        # Save and print results
        runner.save_results(results)
        runner.print_results_summary(results)

        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)
    else:
        # No scenario provided, look for default scenarios
        scenarios_dir = Path("src/scenarios")
        if scenarios_dir.exists():
            scenario_files = list(scenarios_dir.glob("*.json"))
            if scenario_files:
                print(f"\nFound {len(scenario_files)} scenario(s). Running all...\n")
                runner = ScenarioRunner(output_dir=args.output_dir)

                all_passed = True
                for scenario_file in scenario_files:
                    scenario = runner.load_scenario(scenario_file)
                    results = runner.run_scenario(scenario)
                    runner.save_results(results)
                    runner.print_results_summary(results)

                    if not results["success"]:
                        all_passed = False

                sys.exit(0 if all_passed else 1)

        # No scenarios found
        parser.print_help()
        print("\nNo scenario file provided. Use --interactive mode or --list-agents to explore.")
        sys.exit(1)


if __name__ == "__main__":
    main()
