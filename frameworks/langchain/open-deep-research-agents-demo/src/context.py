"""
Research Context Model

Defines the shared context model for managing state across the research workflow.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class WorkflowStage(Enum):
    """Enumeration of workflow stages in the research process."""

    INITIAL = "initial"
    PLANNING = "planning"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    SUMMARIZING = "summarizing"
    WRITING = "writing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"


class ResearchType(Enum):
    """Types of research that can be conducted."""

    GENERAL = "general"
    TECHNICAL = "technical"
    SCIENTIFIC = "scientific"
    MARKET = "market"
    HISTORICAL = "historical"
    COMPARATIVE = "comparative"


@dataclass
class SearchPlan:
    """Represents a search plan with multiple search terms."""

    search_terms: List[str] = field(default_factory=list)
    search_strategy: str = ""
    max_results_per_term: int = 5
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """Represents a single search result."""

    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    relevance_score: float = 0.0
    source: str = "web"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisFindings:
    """Contains analysis findings from the research."""

    key_insights: List[str] = field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    confidence_level: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSection:
    """Represents a section of the research report."""

    title: str
    content: str
    subsections: List["ReportSection"] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Results from the verification process."""

    is_verified: bool = False
    accuracy_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    issues_found: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=datetime.now)


@dataclass
class ResearchContext:
    """
    Central context model for managing state across the research workflow.

    This context is passed between agents and maintains the complete state
    of the research process from initial query to final report.
    """

    # Query Information
    query: str
    research_type: ResearchType = ResearchType.GENERAL
    user_requirements: Dict[str, Any] = field(default_factory=dict)

    # Planning Phase
    search_plan: Optional[SearchPlan] = None

    # Search Phase
    search_results: Dict[str, List[SearchResult]] = field(default_factory=dict)
    search_iterations: int = 0
    total_results_collected: int = 0

    # Analysis Phase
    analysis_findings: Optional[AnalysisFindings] = None
    raw_summaries: List[str] = field(default_factory=list)

    # Report Generation
    report_sections: List[ReportSection] = field(default_factory=list)
    executive_summary: str = ""
    full_report: str = ""
    references: List[str] = field(default_factory=list)

    # Verification
    verification_result: Optional[VerificationResult] = None

    # Workflow Management
    current_stage: WorkflowStage = WorkflowStage.INITIAL
    previous_stages: List[WorkflowStage] = field(default_factory=list)

    # Follow-up and Metadata
    follow_up_questions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing Information
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    stage_timings: Dict[str, float] = field(default_factory=dict)

    def transition_to(self, new_stage: WorkflowStage) -> None:
        """
        Transition to a new workflow stage.

        Args:
            new_stage: The new stage to transition to
        """
        if self.current_stage != new_stage:
            self.previous_stages.append(self.current_stage)
            self.current_stage = new_stage
            self.updated_at = datetime.now()

            # Record timing for the previous stage
            if self.previous_stages:
                prev_stage = self.previous_stages[-1]
                if prev_stage.value not in self.stage_timings:
                    self.stage_timings[prev_stage.value] = 0

    def add_search_results(self, term: str, results: List[SearchResult]) -> None:
        """
        Add search results for a specific search term.

        Args:
            term: The search term used
            results: List of search results
        """
        if term not in self.search_results:
            self.search_results[term] = []
        self.search_results[term].extend(results)
        self.total_results_collected += len(results)
        self.updated_at = datetime.now()

    def add_error(self, error: str) -> None:
        """
        Add an error to the context.

        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.updated_at = datetime.now()

    def add_warning(self, warning: str) -> None:
        """
        Add a warning to the context.

        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)
        self.updated_at = datetime.now()

    def get_all_search_results(self) -> List[SearchResult]:
        """
        Get all search results across all search terms.

        Returns:
            Flat list of all search results
        """
        all_results = []
        for results in self.search_results.values():
            all_results.extend(results)
        return all_results

    def is_complete(self) -> bool:
        """
        Check if the research workflow is complete.

        Returns:
            True if the workflow is in COMPLETE or ERROR stage
        """
        return self.current_stage in [WorkflowStage.COMPLETE, WorkflowStage.ERROR]

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the research process.

        Returns:
            Dictionary containing summary statistics
        """
        return {
            "query": self.query,
            "research_type": self.research_type.value,
            "current_stage": self.current_stage.value,
            "search_terms_used": len(self.search_results),
            "total_results": self.total_results_collected,
            "search_iterations": self.search_iterations,
            "report_sections": len(self.report_sections),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "has_verification": self.verification_result is not None,
            "duration_seconds": (self.updated_at - self.created_at).total_seconds(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the context to a dictionary for serialization.

        Returns:
            Dictionary representation of the context
        """
        return {
            "query": self.query,
            "research_type": self.research_type.value,
            "current_stage": self.current_stage.value,
            "search_plan": {
                "search_terms": self.search_plan.search_terms if self.search_plan else [],
                "strategy": self.search_plan.search_strategy if self.search_plan else "",
            },
            "total_results": self.total_results_collected,
            "executive_summary": self.executive_summary,
            "full_report": self.full_report,
            "verification": {
                "is_verified": self.verification_result.is_verified
                if self.verification_result else False,
                "accuracy_score": self.verification_result.accuracy_score
                if self.verification_result else 0.0,
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "follow_up_questions": self.follow_up_questions,
            "summary_stats": self.get_summary_stats(),
        }