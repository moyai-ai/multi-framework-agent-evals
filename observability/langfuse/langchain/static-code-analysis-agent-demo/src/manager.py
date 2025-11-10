"""
Analysis Manager

Provides a simple interface to run static code analysis on repositories.
"""

import asyncio
import sys
from typing import Dict, Any, Optional

from src.agent import create_agent, run_agent
from src.context import Config, create_initial_context


class AnalysisManager:
    """Manages static code analysis execution."""

    def __init__(self, config: Optional[Config] = None, verbose: bool = True):
        """
        Initialize the Analysis Manager.

        Args:
            config: Optional configuration object
            verbose: Whether to print progress messages
        """
        self.config = config or Config()
        self.verbose = verbose

        # Validate configuration
        self.config.validate()

    async def analyze_repository(
        self,
        repository_url: str,
        analysis_type: str = "security",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scenario_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository.

        Args:
            repository_url: URL of the repository to analyze
            analysis_type: Type of analysis (security, quality, dependencies)
            user_id: Optional user identifier for tracking (enhances observability)
            session_id: Optional session identifier for grouping analyses (enhances observability)
            scenario_name: Optional scenario name for test/evaluation tracking

        Returns:
            Analysis results dictionary
        """
        self._log(f"Starting {analysis_type} analysis for: {repository_url}")
        if scenario_name:
            self._log(f"Scenario: {scenario_name}")

        try:
            # Run the agent
            result = await run_agent(
                repository_url=repository_url,
                analysis_type=analysis_type,
                config=self.config,
                user_id=user_id,
                session_id=session_id,
                scenario_name=scenario_name
            )

            self._log("\nAnalysis completed successfully!")

            # Print summary
            if self.verbose:
                self._print_summary(result)

            return result

        except Exception as e:
            self._log(f"Analysis failed: {e}")
            return {
                "error": str(e),
                "repository": repository_url,
                "analysis_type": analysis_type
            }

    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print analysis summary."""
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Repository: {result.get('repository', 'Unknown')}")
        print(f"Analysis Type: {result.get('analysis_type', 'Unknown')}")
        print(f"Files Analyzed: {len(result.get('files_analyzed', []))}")
        print(f"Issues Found: {len(result.get('issues_found', []))}")
        print(f"Steps Taken: {result.get('steps_taken', 0)}")

        if result.get('error'):
            print(f"Error: {result['error']}")

        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(result.get('final_report', 'No report generated'))
        print("=" * 60)

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)


async def main():
    """Main entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run static code analysis on a GitHub repository"
    )
    parser.add_argument(
        "repository_url",
        help="GitHub repository URL to analyze",
    )
    parser.add_argument(
        "--type",
        dest="analysis_type",
        default="security",
        choices=["security", "quality", "dependencies"],
        help="Type of analysis to perform (default: security)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    parser.add_argument(
        "--user-id",
        dest="user_id",
        default=None,
        help="User identifier for tracking (enhances Langfuse observability)",
    )
    parser.add_argument(
        "--session-id",
        dest="session_id",
        default=None,
        help="Session identifier for grouping analyses (enhances Langfuse observability)",
    )
    parser.add_argument(
        "--scenario",
        dest="scenario_name",
        default=None,
        help="Scenario name for test/evaluation tracking (enhances Langfuse observability)",
    )

    args = parser.parse_args()

    # Create manager
    manager = AnalysisManager(verbose=not args.quiet)

    # Run analysis
    result = await manager.analyze_repository(
        repository_url=args.repository_url,
        analysis_type=args.analysis_type,
        user_id=args.user_id,
        session_id=args.session_id,
        scenario_name=args.scenario_name,
    )

    # Exit with error code if analysis failed
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
