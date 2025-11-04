"""
Claude Agent SDK Quick Start Demo

This module demonstrates the three main usage patterns from the Claude Agent SDK:
1. Basic query
2. Query with custom options
3. Query with tool usage

Now supports running scenarios from individual JSON files in the scenarios directory.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    ToolUseBlock,
)


def load_scenario_files(scenarios_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all scenario JSON files from the scenarios directory.

    Supports both individual scenario files (single scenario object) and
    combined scenario files (object with "scenarios" array).

    Args:
        scenarios_dir: Path to the scenarios directory

    Returns:
        List of scenario dictionaries
    """
    scenarios = []

    # Get all JSON files in the scenarios directory
    json_files = sorted(scenarios_dir.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Check if it's a combined file with "scenarios" array
            if isinstance(data, dict) and "scenarios" in data:
                scenarios.extend(data["scenarios"])
            # Otherwise, it's a single scenario
            elif isinstance(data, dict):
                scenarios.append(data)

            print(f"Loaded scenario from: {json_file.name}")
        except Exception as e:
            print(f"Error loading {json_file.name}: {e}")

    return scenarios


def parse_scenario_options(options_dict: Optional[Dict[str, Any]]) -> Optional[ClaudeAgentOptions]:
    """
    Parse scenario options dictionary into ClaudeAgentOptions object.

    Args:
        options_dict: Dictionary of options from scenario file

    Returns:
        ClaudeAgentOptions object or None if no options
    """
    if not options_dict:
        return None

    return ClaudeAgentOptions(
        system_prompt=options_dict.get("system_prompt"),
        max_turns=options_dict.get("max_turns"),
        allowed_tools=options_dict.get("allowed_tools"),
    )


async def run_scenario(scenario: Dict[str, Any], scenario_index: int, total_scenarios: int) -> Dict[str, Any]:
    """
    Run a single scenario from a JSON file and generate a report.

    Args:
        scenario: Scenario dictionary containing name, prompt, options, etc.
        scenario_index: Index of current scenario (for display)
        total_scenarios: Total number of scenarios (for display)

    Returns:
        Dictionary containing the scenario report data
    """
    print("\n" + "=" * 80)
    print(f"Scenario {scenario_index}/{total_scenarios}: {scenario['name']}")
    print("=" * 80)
    print(f"Description: {scenario.get('description', 'N/A')}")
    print(f"Prompt: {scenario['prompt']}")

    # Initialize report data
    report = {
        "scenario_name": scenario['name'],
        "scenario_index": scenario_index,
        "description": scenario.get('description', 'N/A'),
        "prompt": scenario['prompt'],
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "messages": [],
        "tools_used": [],
        "usage": {},
        "cost_usd": 0.0,
        "error": None
    }

    # Parse options if present
    options = parse_scenario_options(scenario.get("options"))
    if options:
        print(f"Options: system_prompt={bool(options.system_prompt)}, "
              f"max_turns={options.max_turns}, allowed_tools={options.allowed_tools}")
        report["options"] = {
            "system_prompt": options.system_prompt,
            "max_turns": options.max_turns,
            "allowed_tools": options.allowed_tools
        }

    print("-" * 80)

    try:
        # Run the query
        async for message in query(prompt=scenario['prompt'], options=options):
            if isinstance(message, AssistantMessage):
                message_data = {"type": "assistant", "content": []}
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"\nAssistant: {block.text}")
                        message_data["content"].append({
                            "type": "text",
                            "text": block.text
                        })
                    elif isinstance(block, ToolUseBlock):
                        print(f"\nUsing tool: {block.name}")
                        print(f"Tool input: {block.input}")
                        tool_data = {
                            "type": "tool_use",
                            "name": block.name,
                            "input": block.input
                        }
                        message_data["content"].append(tool_data)
                        report["tools_used"].append(block.name)
                report["messages"].append(message_data)

            elif isinstance(message, ResultMessage):
                if message.usage:
                    input_tokens = message.usage.get('input_tokens', 0)
                    output_tokens = message.usage.get('output_tokens', 0)
                    total_tokens = input_tokens + output_tokens
                    print(f"\nTokens used: {total_tokens} (input: {input_tokens}, output: {output_tokens})")
                    report["usage"] = {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens
                    }
                if message.total_cost_usd is not None:
                    print(f"Cost: ${message.total_cost_usd:.4f}")
                    report["cost_usd"] = message.total_cost_usd

        print("\n" + "-" * 80)
        print(f"✓ Scenario '{scenario['name']}' completed")
        report["status"] = "completed"

    except Exception as e:
        print(f"\n✗ Error running scenario '{scenario['name']}': {e}")
        report["status"] = "failed"
        report["error"] = str(e)

    # Save individual scenario report
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Create a safe filename from scenario name
    safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in scenario['name'])
    report_filename = f"{scenario_index:02d}_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = reports_dir / report_filename

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: {report_path}")

    return report


async def run_all_scenarios():
    """Load and run all scenarios from the scenarios directory."""
    print("\n" + "=" * 80)
    print("CLAUDE AGENT SDK - RUNNING ALL SCENARIOS")
    print("=" * 80)

    all_reports = []
    run_timestamp = datetime.now().isoformat()

    try:
        # Load all scenario files
        scenarios_dir = Path(__file__).parent / "scenarios"
        scenarios = load_scenario_files(scenarios_dir)

        if not scenarios:
            print("\nNo scenarios found in the scenarios directory.")
            return

        print(f"\nFound {len(scenarios)} scenario(s) to run\n")

        # Run each scenario
        for i, scenario in enumerate(scenarios, 1):
            report = await run_scenario(scenario, i, len(scenarios))
            all_reports.append(report)

        print("\n" + "=" * 80)
        print(f"All {len(scenarios)} scenarios completed!")
        print("=" * 80 + "\n")

        # Generate summary report
        summary = {
            "run_timestamp": run_timestamp,
            "total_scenarios": len(scenarios),
            "completed": sum(1 for r in all_reports if r["status"] == "completed"),
            "failed": sum(1 for r in all_reports if r["status"] == "failed"),
            "total_cost_usd": sum(r.get("cost_usd", 0.0) for r in all_reports),
            "total_tokens": sum(r.get("usage", {}).get("total_tokens", 0) for r in all_reports),
            "scenarios": all_reports
        }

        # Save summary report
        reports_dir = Path(__file__).parent.parent / "reports"
        summary_filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_path = reports_dir / summary_filename

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary report saved to: {summary_path}")
        print(f"Total cost: ${summary['total_cost_usd']:.4f}")
        print(f"Total tokens: {summary['total_tokens']}")
        print(f"Completed: {summary['completed']}/{summary['total_scenarios']}")
        print(f"Failed: {summary['failed']}/{summary['total_scenarios']}\n")

    except ValueError as e:
        print(f"\nError: {e}")
        print("Please update the .env file with your Anthropic API key.\n")
    except Exception as e:
        print(f"\nUnexpected error: {e}\n")
        import traceback
        traceback.print_exc()


async def example_basic_query():
    """Example 1: Basic query without any options."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Query")
    print("=" * 60)
    print("Prompt: What is 2 + 2?")
    print("-" * 60)

    async for message in query(prompt="What is 2 + 2?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            if message.usage:
                # The usage dict contains input_tokens and output_tokens
                input_tokens = message.usage.get('input_tokens', 0)
                output_tokens = message.usage.get('output_tokens', 0)
                total_tokens = input_tokens + output_tokens
                print(f"\nTokens used: {total_tokens} (input: {input_tokens}, output: {output_tokens})")
            if message.total_cost_usd is not None:
                print(f"Cost: ${message.total_cost_usd:.4f}")


async def example_with_options():
    """Example 2: Query with custom options (system prompt and max turns)."""
    print("\n" + "=" * 60)
    print("Example 2: Query with Custom Options")
    print("=" * 60)
    print("System Prompt: You are a helpful math tutor...")
    print("Prompt: What is 2 + 2?")
    print("-" * 60)

    options = ClaudeAgentOptions(
        system_prompt="You are a helpful math tutor. Explain your reasoning step by step.",
        max_turns=1,
    )

    async for message in query(prompt="What is 2 + 2?", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            if message.usage:
                # The usage dict contains input_tokens and output_tokens
                input_tokens = message.usage.get('input_tokens', 0)
                output_tokens = message.usage.get('output_tokens', 0)
                total_tokens = input_tokens + output_tokens
                print(f"\nTokens used: {total_tokens} (input: {input_tokens}, output: {output_tokens})")
            if message.total_cost_usd is not None:
                print(f"Cost: ${message.total_cost_usd:.4f}")


async def example_with_tools():
    """Example 3: Query that uses built-in tools (Read and Write)."""
    print("\n" + "=" * 60)
    print("Example 3: Query with Tool Usage")
    print("=" * 60)
    print("Prompt: Create a file called test.txt with 'Hello, World!' and read it back")
    print("-" * 60)

    # Use system temp directory
    import tempfile
    temp_dir = Path(tempfile.gettempdir()) / "claude_agent_demo"
    temp_dir.mkdir(exist_ok=True)

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write"],
        max_turns=5,
    )

    prompt = f"Create a file called {temp_dir}/test.txt with the content 'Hello, World!' and then read it back to verify."

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"\nAssistant: {block.text}")
                elif isinstance(block, ToolUseBlock):
                    print(f"\nUsing tool: {block.name}")
                    print(f"Tool input: {block.input}")
        elif isinstance(message, ResultMessage):
            if message.usage:
                # The usage dict contains input_tokens and output_tokens
                input_tokens = message.usage.get('input_tokens', 0)
                output_tokens = message.usage.get('output_tokens', 0)
                total_tokens = input_tokens + output_tokens
                print(f"\nTokens used: {total_tokens} (input: {input_tokens}, output: {output_tokens})")
            if message.total_cost_usd is not None:
                print(f"Cost: ${message.total_cost_usd:.4f}")

    # Clean up
    test_file = temp_dir / "test.txt"
    if test_file.exists():
        test_file.unlink()
        print(f"\nCleaned up: {test_file}")


async def run_all_examples():
    """Run all three examples sequentially."""
    print("\n" + "=" * 60)
    print("CLAUDE AGENT SDK QUICK START EXAMPLES")
    print("=" * 60)

    try:
        await example_basic_query()
        await example_with_options()
        await example_with_tools()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")

    except ValueError as e:
        print(f"\nError: {e}")
        print("Please update the .env file with your Anthropic API key.\n")
    except Exception as e:
        print(f"\nUnexpected error: {e}\n")


def main():
    """
    Main entry point for the demo.

    Runs all scenarios from individual JSON files in the scenarios directory.
    To run the original hardcoded examples, use the --examples flag.
    """
    import sys

    # Check if user wants to run original examples
    if "--examples" in sys.argv:
        asyncio.run(run_all_examples())
    else:
        # Default: run all scenarios from JSON files
        asyncio.run(run_all_scenarios())


if __name__ == "__main__":
    main()
