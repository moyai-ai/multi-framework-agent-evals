"""CLI entrypoint for running Deepeval checks against the Google ADK agent."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import List, Sequence

from google_adk_deepeval_run.paths import (
    AGENT_DEMO_ROOT,
    DEFAULT_REPORTS_DIR,
    DEFAULT_SCENARIO_DIR,
)
from google_adk_deepeval_run.evaluators.deepeval_runner import run_deepeval_for_file
from google_adk_deepeval_run.utils.scenarios import list_scenario_files


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="google-adk-agent-eval",
        description=(
            "Run Deepeval-based checks against the Google ADK code debug agent "
            "using the provided scenario JSON files."
        ),
    )
    parser.add_argument(
        "--scenario-file",
        type=Path,
        default=DEFAULT_SCENARIO_DIR / "sample_python_import_error.json",
        help="Path to the scenario JSON to execute (defaults to sample import error).",
    )
    parser.add_argument(
        "--agent-name",
        type=str,
        default=None,
        help="Optional agent name registered in src/agents.py (e.g., quick_debug_agent).",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Directory where Deepeval reports should be written.",
    )
    parser.add_argument(
        "--env-file",
        action="append",
        type=Path,
        default=[],
        help="Additional .env file(s) to load before running the agent.",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List bundled scenario files from the google-adk agent demo.",
    )
    parser.add_argument(
        "--all-scenarios",
        "--all",
        action="store_true",
        help="Run ALL scenario files in the scenarios directory.",
    )
    return parser


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return _build_parser().parse_args(argv)


def _print_scenarios() -> None:
    print("Available scenario files:\n")
    for file_info in list_scenario_files():
        rel_path = file_info.path.relative_to(AGENT_DEMO_ROOT)
        print(f" • {rel_path} ({file_info.scenario_count} scenario(s))")


def _summarize(result_path: Path, suite_result) -> None:  # type: ignore[arg-type]
    print("\nRun complete!")
    print(f"  Scenario file: {suite_result.scenario_file}")
    print(f"  Agent: {suite_result.agent_name or 'default debug_agent'}")
    print(f"  Scenarios evaluated: {len(suite_result.scenario_results)}")
    print(f"  Overall success rate: {suite_result.overall_success_rate:.2f}")
    print(f"  Report saved to: {result_path}")


def _print_overall_summary(all_results: List) -> None:  # type: ignore[arg-type]
    """Print overall summary across all scenario files."""
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY - ALL SCENARIOS")
    print("=" * 60)
    
    total_scenarios = sum(len(r.scenario_results) for r in all_results)
    total_success_rate = sum(r.overall_success_rate for r in all_results) / len(all_results) if all_results else 0
    
    print(f"Total scenario files: {len(all_results)}")
    print(f"Total scenarios evaluated: {total_scenarios}")
    print(f"Average success rate: {total_success_rate:.2f}")
    
    print("\nPer-file results:")
    for result in all_results:
        status = "✓" if result.overall_success_rate >= 0.7 else "✗"
        print(f"  {status} {Path(result.scenario_file).name}: {result.overall_success_rate:.2f} ({len(result.scenario_results)} scenarios)")
    
    print("=" * 60)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.list_scenarios:
        _print_scenarios()
        return

    reports_dir: Path = args.reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    extra_env_files: List[Path] = [path for path in args.env_file or [] if path.exists()]

    if args.all_scenarios:
        # Run all scenario files in the scenarios directory
        scenario_files = sorted(DEFAULT_SCENARIO_DIR.glob("*.json"))
        
        if not scenario_files:
            print(f"No scenario files found in {DEFAULT_SCENARIO_DIR}")
            return

        print(f"Found {len(scenario_files)} scenario file(s):")
        for file in scenario_files:
            print(f"  - {file.name}")
        print()

        # Run all scenario files
        all_results = []
        for scenario_file in scenario_files:
            print(f"\n{'='*60}")
            print(f"Running scenarios from: {scenario_file.name}")
            print(f"{'='*60}\n")

            try:
                suite_result = asyncio.run(
                    run_deepeval_for_file(
                        scenario_file=scenario_file,
                        agent_name=args.agent_name,
                        output_dir=reports_dir,
                        extra_env_files=extra_env_files,
                    )
                )
                all_results.append(suite_result)
                _summarize(Path(suite_result.report_path), suite_result)
            except Exception as e:
                print(f"Error running scenarios from {scenario_file.name}: {e}")

        # Print overall summary
        if all_results:
            _print_overall_summary(all_results)
        
        return

    scenario_file: Path = args.scenario_file
    if scenario_file.is_dir():
        raise ValueError("Provide a file path, not a directory, for --scenario-file.")

    suite_result = asyncio.run(
        run_deepeval_for_file(
            scenario_file=scenario_file,
            agent_name=args.agent_name,
            output_dir=reports_dir,
            extra_env_files=extra_env_files,
        )
    )

    _summarize(Path(suite_result.report_path), suite_result)


if __name__ == "__main__":
    main()
