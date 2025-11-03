#!/usr/bin/env python
"""Direct scenario runner for lead qualification demos.

Usage:
    uv run python src/run_scenario.py [scenario_name]

Available scenarios:
    single      - Run single lead qualification demo
    batch       - Run batch processing demo
    priority    - Run priority ranking demo
    comparison  - Run scenario comparison demo
    all         - Run all demos sequentially
"""

import asyncio
import sys
from scenarios.demo_runner import DemoRunner
from scenarios.sample_leads import get_sample_leads


async def main():
    """Main entry point for direct scenario execution."""
    # Default to showing help if no scenario specified
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    scenario = sys.argv[1].lower()
    runner = DemoRunner()

    if scenario == "single":
        print("Running Single Lead Qualification Demo...")
        lead = get_sample_leads()[0]
        await runner.run_single_lead_demo(lead)

    elif scenario == "batch":
        print("Running Batch Processing Demo...")
        await runner.run_batch_demo()

    elif scenario == "priority":
        print("Running Priority Ranking Demo...")
        await runner.run_priority_ranking_demo()

    elif scenario == "comparison":
        print("Running Scenario Comparison Demo...")
        await runner.run_scenario_comparison()

    elif scenario == "all":
        print("Running All Demos...")
        await runner.run_all_demos()

    else:
        print(f"Unknown scenario: {scenario}")
        print("\nAvailable scenarios: single, batch, priority, comparison, all")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error running scenario: {e}")
        sys.exit(1)