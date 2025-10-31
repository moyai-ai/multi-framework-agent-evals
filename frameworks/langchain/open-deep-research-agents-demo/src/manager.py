"""
Research Orchestration Manager

Coordinates the execution of research agents through the complete workflow.
"""

import asyncio
import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.context import ResearchContext, WorkflowStage, ResearchType
from src.agents import AGENTS


class ResearchManager:
    """Manages the orchestration of research agents."""

    def __init__(self, verbose: bool = True):
        """
        Initialize the Research Manager.

        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        self.agents = AGENTS

    async def conduct_research(
        self,
        query: str,
        research_type: ResearchType = ResearchType.GENERAL,
        user_requirements: Optional[Dict[str, Any]] = None,
    ) -> ResearchContext:
        """
        Conduct a complete research workflow.

        Args:
            query: The research query
            research_type: Type of research to conduct
            user_requirements: Optional user requirements

        Returns:
            Complete ResearchContext with results
        """
        # Initialize context
        context = ResearchContext(
            query=query,
            research_type=research_type,
            user_requirements=user_requirements or {},
        )

        self._log(f"Starting research for: {query}")
        self._log(f"Research type: {research_type.value}")

        try:
            # Execute workflow stages
            await self._planning_stage(context)
            await self._searching_stage(context)
            await self._analysis_stage(context)
            await self._summarization_stage(context)
            await self._writing_stage(context)
            await self._verification_stage(context)

            # Mark as complete
            context.transition_to(WorkflowStage.COMPLETE)
            self._log("Research completed successfully!")

        except Exception as e:
            context.add_error(f"Research failed: {str(e)}")
            context.transition_to(WorkflowStage.ERROR)
            self._log(f"Research failed with error: {e}")

        # Log summary statistics
        if self.verbose:
            self._print_summary(context)

        return context

    async def _planning_stage(self, context: ResearchContext) -> None:
        """Execute the planning stage."""
        self._log("\n=== PLANNING STAGE ===")
        context.transition_to(WorkflowStage.PLANNING)

        start_time = time.time()

        planner = self.agents["planner"]
        search_plan = await planner.create_search_plan(context)

        context.search_plan = search_plan
        context.stage_timings["planning"] = time.time() - start_time

        self._log(f"Created search plan with {len(search_plan.search_terms)} terms:")
        for term in search_plan.search_terms:
            self._log(f"  - {term}")
        self._log(f"Strategy: {search_plan.search_strategy}")

    async def _searching_stage(self, context: ResearchContext) -> None:
        """Execute the searching stage."""
        self._log("\n=== SEARCHING STAGE ===")
        context.transition_to(WorkflowStage.SEARCHING)

        start_time = time.time()

        searcher = self.agents["search"]
        max_iterations = int(os.getenv("MAX_SEARCH_ITERATIONS", "3"))

        for iteration in range(1, max_iterations + 1):
            self._log(f"Search iteration {iteration}/{max_iterations}")

            search_results = await searcher.conduct_searches(context)

            # Add results to context
            for term, results in search_results.items():
                context.add_search_results(term, results)

            context.search_iterations = iteration

            # Check if we have enough results
            if context.total_results_collected >= 15:
                self._log(f"Collected sufficient results: {context.total_results_collected}")
                break

        context.stage_timings["searching"] = time.time() - start_time
        self._log(f"Search complete. Total results: {context.total_results_collected}")

    async def _analysis_stage(self, context: ResearchContext) -> None:
        """Execute the analysis stage."""
        self._log("\n=== ANALYSIS STAGE ===")
        context.transition_to(WorkflowStage.ANALYZING)

        start_time = time.time()

        analyst = self.agents["analyst"]
        analysis = await analyst.analyze_results(context)

        context.analysis_findings = analysis
        context.stage_timings["analyzing"] = time.time() - start_time

        self._log(f"Analysis complete:")
        self._log(f"  - Key insights: {len(analysis.key_insights)}")
        self._log(f"  - Confidence: {analysis.confidence_level:.2%}")
        if analysis.contradictions:
            self._log(f"  - Contradictions found: {len(analysis.contradictions)}")
        if analysis.gaps:
            self._log(f"  - Knowledge gaps: {len(analysis.gaps)}")

    async def _summarization_stage(self, context: ResearchContext) -> None:
        """Execute the summarization stage."""
        self._log("\n=== SUMMARIZATION STAGE ===")
        context.transition_to(WorkflowStage.SUMMARIZING)

        start_time = time.time()

        summarizer = self.agents["summarizer"]
        summaries = await summarizer.create_summaries(context)

        context.raw_summaries = summaries
        if summaries:
            context.executive_summary = summaries[0][:500]  # First 500 chars as exec summary

        context.stage_timings["summarizing"] = time.time() - start_time
        self._log(f"Created {len(summaries)} summaries")

    async def _writing_stage(self, context: ResearchContext) -> None:
        """Execute the writing stage."""
        self._log("\n=== WRITING STAGE ===")
        context.transition_to(WorkflowStage.WRITING)

        start_time = time.time()

        writer = self.agents["writer"]
        report = await writer.write_report(context)

        context.full_report = report

        # Extract sections from report (simplified)
        sections = report.split("##")
        for section in sections[1:]:  # Skip first empty split
            lines = section.strip().split("\n")
            if lines:
                title = lines[0].strip()
                content = "\n".join(lines[1:])
                context.report_sections.append({
                    "title": title,
                    "content": content,
                })

        context.stage_timings["writing"] = time.time() - start_time
        self._log(f"Report written: {len(report)} characters")
        self._log(f"Report sections: {len(context.report_sections)}")

    async def _verification_stage(self, context: ResearchContext) -> None:
        """Execute the verification stage."""
        self._log("\n=== VERIFICATION STAGE ===")
        context.transition_to(WorkflowStage.VERIFYING)

        start_time = time.time()

        verifier = self.agents["verifier"]
        verification = await verifier.verify_research(context)

        context.verification_result = verification
        context.stage_timings["verifying"] = time.time() - start_time

        self._log(f"Verification complete:")
        self._log(f"  - Verified: {verification.is_verified}")
        self._log(f"  - Accuracy: {verification.accuracy_score:.2%}")
        self._log(f"  - Completeness: {verification.completeness_score:.2%}")
        self._log(f"  - Consistency: {verification.consistency_score:.2%}")

        if verification.issues_found:
            self._log(f"  - Issues found: {len(verification.issues_found)}")
            for issue in verification.issues_found[:3]:
                self._log(f"    • {issue}")

        if verification.suggestions:
            self._log(f"  - Suggestions: {len(verification.suggestions)}")
            for suggestion in verification.suggestions[:3]:
                self._log(f"    • {suggestion}")

    def _log(self, message: str) -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def _print_summary(self, context: ResearchContext) -> None:
        """Print a summary of the research process."""
        print("\n" + "=" * 60)
        print("RESEARCH SUMMARY")
        print("=" * 60)

        stats = context.get_summary_stats()
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        # Print timing information
        if context.stage_timings:
            print("\nStage Timings:")
            for stage, duration in context.stage_timings.items():
                print(f"  {stage.title()}: {duration:.2f} seconds")

        print("=" * 60)


async def main():
    """Main entry point for command-line execution."""
    import sys

    # Check for command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python -m src.manager 'Your research query here'")
        print("\nExample: python -m src.manager 'What are the latest developments in AI?'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Determine research type based on query content
    research_type = ResearchType.GENERAL
    if any(word in query.lower() for word in ["technology", "tech", "software", "hardware"]):
        research_type = ResearchType.TECHNICAL
    elif any(word in query.lower() for word in ["science", "research", "study", "experiment"]):
        research_type = ResearchType.SCIENTIFIC
    elif any(word in query.lower() for word in ["market", "business", "economy", "finance"]):
        research_type = ResearchType.MARKET
    elif any(word in query.lower() for word in ["history", "historical", "past", "ancient"]):
        research_type = ResearchType.HISTORICAL
    elif any(word in query.lower() for word in ["compare", "versus", "vs", "difference"]):
        research_type = ResearchType.COMPARATIVE

    # Create manager and conduct research
    manager = ResearchManager(verbose=True)
    context = await manager.conduct_research(query, research_type)

    # Print the final report
    print("\n" + "=" * 60)
    print("FINAL RESEARCH REPORT")
    print("=" * 60)
    print(context.full_report)

    # Print follow-up questions if any
    if context.follow_up_questions:
        print("\n" + "=" * 60)
        print("FOLLOW-UP QUESTIONS")
        print("=" * 60)
        for i, question in enumerate(context.follow_up_questions, 1):
            print(f"{i}. {question}")


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())