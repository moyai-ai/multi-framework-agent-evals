"""
Context models for the Financial Research Agent System with Langfuse Tracing.

This module defines the context structure that maintains state throughout
the financial research workflow across multiple agents, with added tracing metadata.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class FinancialResearchContext:
    """
    Context for financial research conversations with tracing support.

    This context is passed between agents and accumulates information
    throughout the research workflow. It now includes trace_id for Langfuse tracking.
    """
    # User query and metadata
    query: str = ""
    company_name: Optional[str] = None
    analysis_type: Optional[str] = None  # e.g., "company_analysis", "market_research"

    # Planning phase
    search_plan: List[str] = field(default_factory=list)  # List of search terms

    # Search phase
    search_results: Dict[str, str] = field(default_factory=dict)  # term -> results

    # Analysis phase
    financials_analysis: Optional[str] = None
    risk_analysis: Optional[str] = None

    # Writing phase
    report_sections: Dict[str, str] = field(default_factory=dict)  # section -> content
    executive_summary: Optional[str] = None
    full_report: Optional[str] = None

    # Verification phase
    verification_status: Optional[str] = None  # "passed", "failed", "needs_revision"
    verification_notes: List[str] = field(default_factory=list)

    # Follow-up
    follow_up_questions: List[str] = field(default_factory=list)

    # Workflow tracking
    current_stage: str = "initial"  # initial, planning, searching, analyzing, writing, verifying, complete
    session_id: Optional[str] = None

    # Langfuse tracing metadata
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    parent_observation_id: Optional[str] = None


def create_initial_context(
    query: str = "",
    session_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> FinancialResearchContext:
    """
    Create a new initial context for a financial research session with tracing.

    Args:
        query: The user's research query
        session_id: Optional session identifier
        trace_id: Optional Langfuse trace ID
        user_id: Optional user identifier for Langfuse

    Returns:
        FinancialResearchContext: A new context instance
    """
    return FinancialResearchContext(
        query=query,
        session_id=session_id or f"session_{id(object())}",
        current_stage="initial",
        trace_id=trace_id,
        user_id=user_id
    )


def create_test_context(**kwargs) -> FinancialResearchContext:
    """
    Create a context with specific test values.

    Args:
        **kwargs: Field values to set in the context

    Returns:
        FinancialResearchContext: Context with specified values
    """
    context = create_initial_context()
    for key, value in kwargs.items():
        if hasattr(context, key):
            setattr(context, key, value)
    return context


def context_diff(old_context: FinancialResearchContext, new_context: FinancialResearchContext) -> Dict[str, Any]:
    """
    Calculate the difference between two contexts.

    Args:
        old_context: Previous context state
        new_context: Current context state

    Returns:
        Dict with fields that changed and their new values
    """
    diff = {}

    # Compare all fields
    for field_name in old_context.__dataclass_fields__:
        old_value = getattr(old_context, field_name)
        new_value = getattr(new_context, field_name)

        if old_value != new_value:
            diff[field_name] = new_value

    return diff


def format_context_summary(context: FinancialResearchContext) -> str:
    """
    Format a human-readable summary of the context.

    Args:
        context: The context to summarize

    Returns:
        str: Formatted summary
    """
    summary_lines = [
        f"Query: {context.query}",
        f"Company: {context.company_name or 'N/A'}",
        f"Analysis Type: {context.analysis_type or 'N/A'}",
        f"Current Stage: {context.current_stage}",
        f"Search Terms: {len(context.search_plan)}",
        f"Search Results: {len(context.search_results)}",
        f"Report Sections: {len(context.report_sections)}",
        f"Verification Status: {context.verification_status or 'Not verified'}",
        f"Follow-up Questions: {len(context.follow_up_questions)}",
        f"Trace ID: {context.trace_id or 'N/A'}"
    ]

    return "\n".join(summary_lines)
