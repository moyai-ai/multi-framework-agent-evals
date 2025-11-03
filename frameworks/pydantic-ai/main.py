#!/usr/bin/env python
"""Main entry point for the Pydantic AI Bank Support Demo."""

import asyncio
import sys
from pathlib import Path


async def main():
    """Main entry point."""
    print("🏦 Pydantic AI Bank Support Demo")
    print("=" * 40)
    print("\nAvailable commands:")
    print("  1. Initialize database:  python -m src.database_init")
    print("  2. Run scenarios:        python -m src.runner src/scenarios/ -v")
    print("  3. Run tests:           pytest tests/ -v")
    print("\nFor detailed usage, see README.md")

    # If running directly, show a simple interactive menu
    if len(sys.argv) == 1:
        print("\nWhat would you like to do?")
        print("1. Initialize database")
        print("2. Run all scenarios")
        print("3. Run authentication scenario")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ")

        if choice == "1":
            from src.database_init import initialize_database
            await initialize_database()
        elif choice == "2":
            from src.runner import ScenarioRunner
            runner = ScenarioRunner(verbose=True)
            scenarios_dir = Path(__file__).parent / "src" / "scenarios"
            await runner.run_all_scenarios(str(scenarios_dir))
        elif choice == "3":
            from src.runner import ScenarioRunner
            runner = ScenarioRunner(verbose=True)
            scenario_path = Path(__file__).parent / "src" / "scenarios" / "authentication_flow.json"
            await runner.run_scenario(str(scenario_path))
        elif choice == "4":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please run with specific commands as shown above.")


if __name__ == "__main__":
    asyncio.run(main())