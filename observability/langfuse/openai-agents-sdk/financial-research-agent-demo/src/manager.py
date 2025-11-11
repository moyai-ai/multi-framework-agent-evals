"""
Financial Research Manager with Full Langfuse Observability.

This module orchestrates the multi-agent research workflow with comprehensive
tracing at every level:
- Trace-level: Overall research workflow
- Span-level: Each agent execution
- Generation-level: LLM calls within agents
- Tool-level: Function tool executions

This provides complete visibility into the multi-agent system's behavior.
"""

import asyncio
import sys
from typing import List, Dict, Optional
from datetime import datetime

from agents import Runner, MessageOutputItem, RunConfig
from langfuse import observe, get_client

from .context import FinancialResearchContext, create_initial_context
from .agents import (
    planner_agent,
    search_agent,
    writer_agent,
    verifier_agent,
    AGENTS
)


class FinancialResearchManager:
    """
    Manages the complete financial research workflow with full Langfuse tracing.

    Each major step in the workflow is instrumented with Langfuse spans,
    providing complete observability of the multi-agent system.
    """

    def __init__(self, verbose: bool = True, user_id: Optional[str] = None):
        """
        Initialize the research manager with Langfuse client.

        Args:
            verbose: Whether to print detailed progress information
            user_id: Optional user ID for Langfuse tracing
        """
        self.verbose = verbose
        self.context = None
        self.user_id = user_id or "default-user"
        self.langfuse = get_client()

    def _print(self, message: str, prefix: str = ""):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            if prefix:
                print(f"{prefix} {message}")
            else:
                print(message)

    def _print_section(self, title: str):
        """Print a section header."""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"{title}")
            print(f"{'='*60}\n")

    @observe(name="financial_research_workflow")
    async def run(self, query: str) -> Dict[str, any]:
        """
        Execute the complete financial research workflow with full tracing.

        This is the top-level trace that contains all sub-spans for the workflow.

        Args:
            query: User's research query

        Returns:
            Dict containing the research results
        """
        self._print_section(f"Financial Research: {query}")

        # Get Langfuse client and update trace metadata
        langfuse = get_client()
        langfuse.update_current_trace(
            name="Financial Research Workflow",
            user_id=self.user_id,
            tags=["financial-research", "multi-agent"],
            metadata={
                "query": query,
                "agent_count": len(AGENTS),
                "framework": "openai-agents-sdk"
            }
        )

        # Initialize context with trace ID
        trace_id = langfuse.get_current_trace_id()
        self.context = create_initial_context(
            query=query,
            trace_id=trace_id,
            user_id=self.user_id
        )
        start_time = datetime.now()

        try:
            # Step 1: Plan searches
            self._print("Step 1: Planning search strategy...", "📋")
            search_plan = await self._plan_searches(query)
            self.context.search_plan = search_plan
            self.context.current_stage = "searching"
            self._print(f"Generated {len(search_plan)} search terms")

            # Step 2: Perform searches
            self._print("\nStep 2: Executing searches...", "🔍")
            search_results = await self._perform_searches(search_plan)
            self.context.search_results = search_results
            self.context.current_stage = "writing"
            self._print(f"Completed {len(search_results)} searches")

            # Step 3: Write report
            self._print("\nStep 3: Writing comprehensive report...", "📝")
            report = await self._write_report(query, search_results)
            self.context.full_report = report
            self.context.current_stage = "verifying"

            # Step 4: Verify report
            self._print("\nStep 4: Verifying report quality...", "✓")
            verification = await self._verify_report(report)
            self.context.verification_status = verification.get("status", "unknown")
            self.context.verification_notes = verification.get("notes", [])
            self.context.current_stage = "complete"

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Update trace with final results
            langfuse.update_current_trace(
                output={
                    "report_length": len(report),
                    "verification_status": verification.get("status"),
                    "execution_time": execution_time,
                    "follow_up_questions": self.context.follow_up_questions
                },
                metadata={
                    "completed_successfully": True,
                    "stages_completed": [
                        "planning",
                        "searching",
                        "writing",
                        "verifying"
                    ]
                }
            )

            # Print final report
            self._print_section("FINAL REPORT")
            self._print(report)

            if self.context.follow_up_questions:
                self._print_section("FOLLOW-UP QUESTIONS")
                for i, question in enumerate(self.context.follow_up_questions, 1):
                    self._print(f"{i}. {question}")

            self._print_section("VERIFICATION RESULTS")
            self._print(f"Status: {verification.get('status', 'unknown')}")
            if verification.get('notes'):
                for note in verification['notes']:
                    self._print(f"  • {note}")

            self._print(f"\n✅ Research completed in {execution_time:.1f} seconds")
            self._print(f"📊 Trace ID: {trace_id}")

            return {
                "query": query,
                "report": report,
                "verification": verification,
                "follow_up_questions": self.context.follow_up_questions,
                "execution_time": execution_time,
                "context": self.context,
                "trace_id": trace_id
            }

        except Exception as e:
            self._print(f"\n❌ Error during research: {e}", "")
            # Update trace with error information
            langfuse.update_current_trace(
                metadata={"error": str(e), "completed_successfully": False}
            )
            raise

    @observe(name="plan_searches", as_type="chain")
    async def _plan_searches(self, query: str) -> List[str]:
        """
        Use the planner agent to generate search terms (traced as a chain).

        Args:
            query: User's research query

        Returns:
            List of search terms
        """
        langfuse = get_client()
        langfuse.update_current_span(
            input={"query": query},
            metadata={"agent": "planner", "step": "planning"}
        )

        prompt = f"Generate 3-4 search terms for this financial research query: {query}"

        result = await Runner.run(
            planner_agent,
            [{"role": "user", "content": prompt}],
            context=self.context,
            run_config=RunConfig(workflow_name="Financial Research Agent Workflow")
        )

        # Extract search terms from response
        search_terms = []
        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                content = " ".join(
                    content_item.text for content_item in item.raw_item.content
                    if hasattr(content_item, 'text')
                )
                # Parse search terms (each line starting with - or number)
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•'):
                        term = line[1:].strip()
                        if term:
                            search_terms.append(term)
                    elif line and line[0].isdigit() and '.' in line:
                        term = line.split('.', 1)[1].strip()
                        if term:
                            search_terms.append(term)

        # Fallback if parsing fails
        if not search_terms:
            self._print("Warning: Could not parse search terms, using defaults")
            search_terms = [
                f"{query} financial analysis",
                f"{query} market trends",
                f"{query} competitive position"
            ]

        if self.verbose:
            for term in search_terms:
                self._print(f"  • {term}")

        # Update observation with output
        langfuse.update_current_span(
            output={"search_terms": search_terms, "count": len(search_terms)}
        )

        return search_terms

    @observe(name="perform_searches", as_type="chain")
    async def _perform_searches(self, search_terms: List[str]) -> Dict[str, str]:
        """
        Execute searches concurrently for all search terms (traced as a chain).

        Args:
            search_terms: List of search terms

        Returns:
            Dict mapping search term to results
        """
        langfuse = get_client()
        langfuse.update_current_span(
            input={"search_terms": search_terms, "count": len(search_terms)},
            metadata={"agent": "search", "step": "searching", "concurrent": True}
        )

        # Create search tasks
        tasks = [self._search(term) for term in search_terms]

        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build results dict
        search_results = {}
        for term, result in zip(search_terms, results):
            if isinstance(result, Exception):
                self._print(f"  ⚠️ Error searching '{term}': {result}")
                search_results[term] = f"Error: {str(result)}"
            else:
                self._print(f"  ✓ {term}")
                search_results[term] = result

        # Update observation with output
        langfuse.update_current_span(
            output={
                "search_results": {k: len(v) for k, v in search_results.items()},
                "successful_searches": len([r for r in results if not isinstance(r, Exception)])
            }
        )

        return search_results

    @observe(name="search_single_term", as_type="agent")
    async def _search(self, search_term: str) -> str:
        """
        Execute a single search using the search agent (traced as agent).

        Args:
            search_term: Term to search for

        Returns:
            Search results
        """
        langfuse = get_client()
        langfuse.update_current_span(
            input={"search_term": search_term},
            metadata={"agent": "search"}
        )

        prompt = f"Search for: {search_term}"

        result = await Runner.run(
            search_agent,
            [{"role": "user", "content": prompt}],
            context=self.context,
            run_config=RunConfig(workflow_name="Financial Research Agent Workflow")
        )

        # Extract search results
        results_text = ""
        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                results_text += " ".join(
                    content_item.text for content_item in item.raw_item.content
                    if hasattr(content_item, 'text')
                )

        output_text = results_text if results_text else "No results found"

        # Update observation with output
        langfuse.update_current_span(
            output={"results": output_text, "length": len(output_text)}
        )

        return output_text

    @observe(name="write_report", as_type="agent")
    async def _write_report(self, query: str, search_results: Dict[str, str]) -> str:
        """
        Use the writer agent to synthesize a comprehensive report (traced as agent).

        Args:
            query: Original research query
            search_results: Results from all searches

        Returns:
            Formatted report
        """
        langfuse = get_client()
        langfuse.update_current_span(
            input={
                "query": query,
                "search_results_count": len(search_results)
            },
            metadata={"agent": "writer", "step": "writing"}
        )

        # Format search results for the writer
        formatted_results = "Search Results:\n\n"
        for term, results in search_results.items():
            formatted_results += f"=== {term} ===\n{results}\n\n"

        prompt = f"""
Write a comprehensive financial research report for: {query}

{formatted_results}

CRITICAL INSTRUCTIONS:
1. ALWAYS use the company_financials_tool to get accurate financial data - do not make up numbers
2. ALWAYS use the risk_analysis_tool to get proper risk assessment - do not guess risks
3. Use the EXACT numbers from the tool outputs - ensure consistency across all sections
4. Include source attribution in each section (e.g., "Based on financial analysis tools and search results")
5. Follow the report structure provided in your instructions
6. Include an executive summary and 2-3 follow-up research questions
7. Ensure all financial metrics are consistent - use the same numbers throughout the report

Remember: Use the tools to get real data, then cite your sources in the report.
"""

        result = await Runner.run(
            writer_agent,
            [{"role": "user", "content": prompt}],
            context=self.context,
            run_config=RunConfig(workflow_name="Financial Research Agent Workflow")
        )

        # Extract report
        report = ""
        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                report += " ".join(
                    content_item.text for content_item in item.raw_item.content
                    if hasattr(content_item, 'text')
                )

        # Extract follow-up questions from report
        self._extract_follow_up_questions(report)

        output_report = report if report else "Error: No report generated"

        # Update observation with output
        langfuse.update_current_span(
            output={
                "report": output_report,
                "length": len(output_report),
                "follow_up_questions": self.context.follow_up_questions
            }
        )

        return output_report

    @observe(name="verify_report", as_type="agent")
    async def _verify_report(self, report: str) -> Dict[str, any]:
        """
        Use the verifier agent to validate the report (traced as agent).

        Args:
            report: The report to verify

        Returns:
            Verification results
        """
        langfuse = get_client()
        langfuse.update_current_span(
            input={"report_length": len(report)},
            metadata={"agent": "verifier", "step": "verifying"}
        )

        prompt = f"""
Verify this financial research report for quality and consistency:

{report}

Provide verification status and any issues found.
"""

        result = await Runner.run(
            verifier_agent,
            [{"role": "user", "content": prompt}],
            context=self.context,
            run_config=RunConfig(workflow_name="Financial Research Agent Workflow")
        )

        # Extract verification results
        verification_text = ""
        for item in result.new_items:
            if isinstance(item, MessageOutputItem):
                verification_text += " ".join(
                    content_item.text for content_item in item.raw_item.content
                    if hasattr(content_item, 'text')
                )

        # Parse verification status
        status = "PASSED" if "PASSED" in verification_text.upper() else "NEEDS REVISION"

        verification_result = {
            "status": status,
            "notes": [verification_text],
            "raw": verification_text
        }

        # Update observation with output
        langfuse.update_current_span(
            output=verification_result
        )

        return verification_result

    def _extract_follow_up_questions(self, report: str):
        """Extract follow-up questions from the report."""
        lines = report.split('\n')
        in_followup_section = False
        questions = []

        for line in lines:
            line = line.strip()
            if 'follow-up' in line.lower() and 'question' in line.lower():
                in_followup_section = True
                continue

            if in_followup_section:
                if line.startswith('-') or line.startswith('•'):
                    questions.append(line[1:].strip())
                elif line and line[0].isdigit() and '.' in line:
                    questions.append(line.split('.', 1)[1].strip())
                elif line.startswith('#'):
                    # Next section started
                    break

        self.context.follow_up_questions = questions[:3]  # Keep top 3


async def main():
    """
    Main entry point for interactive financial research with Langfuse tracing.
    """
    print("Financial Research Multi-Agent System with Langfuse Observability")
    print("=" * 60)

    # Get query from user
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("\nEnter your financial research query: ")

    if not query.strip():
        print("Error: No query provided")
        sys.exit(1)

    # Run research
    manager = FinancialResearchManager(verbose=True)
    try:
        result = await manager.run(query)
        print(f"\n\nView your trace in Langfuse: https://cloud.langfuse.com/trace/{result['trace_id']}")
    except Exception as e:
        print(f"\n❌ Research failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
