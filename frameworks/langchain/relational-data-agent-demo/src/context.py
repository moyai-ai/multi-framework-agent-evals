"""
Context Management

Manages conversation context and query history for the relational data agents.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum


class QueryType(str, Enum):
    """Types of database queries."""

    SIMPLE_SELECT = "simple_select"
    JOIN = "join"
    AGGREGATION = "aggregation"
    COMPLEX = "complex"
    ANALYSIS = "analysis"


class QueryResult(BaseModel):
    """Represents a query execution result."""

    query: str
    query_type: QueryType
    success: bool
    result_count: Optional[int] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalysisInsight(BaseModel):
    """Represents an analytical insight from data."""

    insight_type: str  # trend, anomaly, correlation, summary
    description: str
    supporting_data: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    related_queries: List[str] = Field(default_factory=list)


class ConversationContext(BaseModel):
    """Manages the context of a database query conversation."""

    session_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # User request information
    original_request: str
    interpreted_intent: Optional[str] = None

    # Query history
    query_history: List[QueryResult] = Field(default_factory=list)

    # Database schema context
    tables_referenced: List[str] = Field(default_factory=list)
    columns_referenced: List[str] = Field(default_factory=list)
    relationships_used: List[str] = Field(default_factory=list)

    # Analysis context
    insights: List[AnalysisInsight] = Field(default_factory=list)

    # Current state
    current_stage: str = "initial"  # initial, planning, querying, analyzing, reporting
    requires_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)

    # Preferences and constraints
    max_results: int = 100
    output_format: str = "table"  # table, json, summary, report
    safety_mode: bool = True

    def add_query_result(self, query_result: QueryResult):
        """Add a query result to the history."""
        self.query_history.append(query_result)

        # Extract tables and columns from the query
        # This is a simplified extraction - in production, use SQL parser
        query_upper = query_result.query.upper()
        if "FROM" in query_upper:
            # Basic table extraction
            from_idx = query_upper.index("FROM")
            after_from = query_upper[from_idx + 4:].strip()
            table_part = after_from.split()[0].strip(",")
            if table_part not in self.tables_referenced:
                self.tables_referenced.append(table_part.lower())

    def add_insight(self, insight: AnalysisInsight):
        """Add an analytical insight."""
        self.insights.append(insight)

    def get_recent_queries(self, n: int = 5) -> List[QueryResult]:
        """Get the n most recent queries."""
        return self.query_history[-n:] if self.query_history else []

    def get_successful_queries(self) -> List[QueryResult]:
        """Get all successful queries from history."""
        return [q for q in self.query_history if q.success]

    def needs_clarification(self, questions: List[str]) -> None:
        """Mark that clarification is needed from the user."""
        self.requires_clarification = True
        self.clarification_questions = questions

    def resolve_clarification(self) -> None:
        """Mark that clarification has been resolved."""
        self.requires_clarification = False
        self.clarification_questions = []

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary of the context."""
        return {
            "session_id": self.session_id,
            "duration_seconds": (datetime.now(timezone.utc) - self.started_at).total_seconds(),
            "original_request": self.original_request,
            "queries_executed": len(self.query_history),
            "successful_queries": len(self.get_successful_queries()),
            "tables_accessed": self.tables_referenced,
            "insights_generated": len(self.insights),
            "current_stage": self.current_stage,
        }


class QueryPlan(BaseModel):
    """Represents a plan for executing database queries."""

    description: str
    steps: List[Dict[str, str]]  # List of step descriptions and queries
    estimated_complexity: str  # simple, moderate, complex
    requires_joins: bool = False
    requires_aggregation: bool = False
    requires_subqueries: bool = False
    optimization_notes: Optional[str] = None


class ContextManager:
    """Manages multiple conversation contexts."""

    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        self.active_context_id: Optional[str] = None

    def create_context(self, session_id: str, request: str) -> ConversationContext:
        """Create a new conversation context."""
        context = ConversationContext(
            session_id=session_id,
            original_request=request
        )
        self.contexts[session_id] = context
        self.active_context_id = session_id
        return context

    def get_context(self, session_id: Optional[str] = None) -> Optional[ConversationContext]:
        """Get a context by session ID or the active context."""
        if session_id:
            return self.contexts.get(session_id)
        elif self.active_context_id:
            return self.contexts.get(self.active_context_id)
        return None

    def update_stage(self, stage: str, session_id: Optional[str] = None):
        """Update the current stage of a context."""
        context = self.get_context(session_id)
        if context:
            context.current_stage = stage

    def clear_context(self, session_id: str):
        """Clear a specific context."""
        if session_id in self.contexts:
            del self.contexts[session_id]
            if self.active_context_id == session_id:
                self.active_context_id = None

    def get_all_contexts(self) -> Dict[str, ConversationContext]:
        """Get all contexts."""
        return self.contexts

    def summarize_all_contexts(self) -> List[Dict[str, Any]]:
        """Get summaries of all contexts."""
        return [context.to_summary() for context in self.contexts.values()]


# Global context manager instance
context_manager = ContextManager()


def create_test_context() -> ConversationContext:
    """Create a test context for development."""
    return ConversationContext(
        session_id="test_session",
        original_request="Show me the top 5 customers by total order value"
    )