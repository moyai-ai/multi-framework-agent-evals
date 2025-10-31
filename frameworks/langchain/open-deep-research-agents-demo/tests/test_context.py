"""
Tests for Research Context

Tests for the ResearchContext data model and its methods.
"""

import pytest
from datetime import datetime

from src.context import (
    ResearchContext,
    WorkflowStage,
    ResearchType,
    SearchPlan,
    SearchResult,
    AnalysisFindings,
    ReportSection,
    VerificationResult,
)


class TestResearchContext:
    """Test ResearchContext functionality."""

    def test_context_initialization(self):
        """Test context initialization with default values."""
        context = ResearchContext(query="Test query")

        assert context.query == "Test query"
        assert context.research_type == ResearchType.GENERAL
        assert context.current_stage == WorkflowStage.INITIAL
        assert context.total_results_collected == 0
        assert len(context.errors) == 0
        assert len(context.warnings) == 0

    def test_transition_to_stage(self, sample_context):
        """Test transitioning between workflow stages."""
        initial_stage = sample_context.current_stage

        sample_context.transition_to(WorkflowStage.PLANNING)

        assert sample_context.current_stage == WorkflowStage.PLANNING
        assert initial_stage in sample_context.previous_stages

    def test_add_search_results(self, sample_context, sample_search_results):
        """Test adding search results."""
        term = "test search"
        sample_context.add_search_results(term, sample_search_results)

        assert term in sample_context.search_results
        assert len(sample_context.search_results[term]) == len(sample_search_results)
        assert sample_context.total_results_collected == len(sample_search_results)

    def test_add_error(self, sample_context):
        """Test adding errors."""
        error_msg = "Test error"
        sample_context.add_error(error_msg)

        assert error_msg in sample_context.errors
        assert len(sample_context.errors) == 1

    def test_add_warning(self, sample_context):
        """Test adding warnings."""
        warning_msg = "Test warning"
        sample_context.add_warning(warning_msg)

        assert warning_msg in sample_context.warnings
        assert len(sample_context.warnings) == 1

    def test_get_all_search_results(self, sample_context, sample_search_results):
        """Test getting all search results."""
        sample_context.add_search_results("term1", sample_search_results[:2])
        sample_context.add_search_results("term2", sample_search_results[2:])

        all_results = sample_context.get_all_search_results()

        assert len(all_results) == len(sample_search_results)
        assert all(isinstance(r, SearchResult) for r in all_results)

    def test_is_complete(self, sample_context):
        """Test checking if workflow is complete."""
        assert not sample_context.is_complete()

        sample_context.transition_to(WorkflowStage.COMPLETE)
        assert sample_context.is_complete()

        sample_context.transition_to(WorkflowStage.ERROR)
        assert sample_context.is_complete()

    def test_get_summary_stats(self, sample_context, sample_search_results):
        """Test getting summary statistics."""
        sample_context.add_search_results("term1", sample_search_results)
        sample_context.add_error("Test error")
        sample_context.add_warning("Test warning")

        stats = sample_context.get_summary_stats()

        assert stats["query"] == sample_context.query
        assert stats["research_type"] == sample_context.research_type.value
        assert stats["total_results"] == len(sample_search_results)
        assert stats["errors"] == 1
        assert stats["warnings"] == 1

    def test_to_dict(self, complete_context):
        """Test converting context to dictionary."""
        context_dict = complete_context.to_dict()

        assert isinstance(context_dict, dict)
        assert context_dict["query"] == complete_context.query
        assert context_dict["research_type"] == complete_context.research_type.value
        assert context_dict["current_stage"] == complete_context.current_stage.value
        assert "summary_stats" in context_dict


class TestWorkflowStage:
    """Test WorkflowStage enum."""

    def test_workflow_stages(self):
        """Test all workflow stages are defined."""
        expected_stages = [
            "INITIAL",
            "PLANNING",
            "SEARCHING",
            "ANALYZING",
            "SUMMARIZING",
            "WRITING",
            "VERIFYING",
            "COMPLETE",
            "ERROR",
        ]

        for stage_name in expected_stages:
            assert hasattr(WorkflowStage, stage_name)
            stage = getattr(WorkflowStage, stage_name)
            assert stage.value == stage_name.lower()


class TestResearchType:
    """Test ResearchType enum."""

    def test_research_types(self):
        """Test all research types are defined."""
        expected_types = [
            "GENERAL",
            "TECHNICAL",
            "SCIENTIFIC",
            "MARKET",
            "HISTORICAL",
            "COMPARATIVE",
        ]

        for type_name in expected_types:
            assert hasattr(ResearchType, type_name)
            research_type = getattr(ResearchType, type_name)
            assert research_type.value == type_name.lower()


class TestSearchPlan:
    """Test SearchPlan dataclass."""

    def test_search_plan_initialization(self):
        """Test SearchPlan initialization."""
        terms = ["term1", "term2", "term3"]
        strategy = "Test strategy"

        plan = SearchPlan(
            search_terms=terms,
            search_strategy=strategy,
            max_results_per_term=10,
        )

        assert plan.search_terms == terms
        assert plan.search_strategy == strategy
        assert plan.max_results_per_term == 10
        assert isinstance(plan.created_at, datetime)


class TestSearchResult:
    """Test SearchResult dataclass."""

    def test_search_result_initialization(self):
        """Test SearchResult initialization."""
        result = SearchResult(
            url="https://example.com",
            title="Test Title",
            snippet="Test snippet",
            content="Full content",
            relevance_score=0.95,
            source="test",
        )

        assert result.url == "https://example.com"
        assert result.title == "Test Title"
        assert result.snippet == "Test snippet"
        assert result.content == "Full content"
        assert result.relevance_score == 0.95
        assert result.source == "test"


class TestAnalysisFindings:
    """Test AnalysisFindings dataclass."""

    def test_analysis_findings_initialization(self):
        """Test AnalysisFindings initialization."""
        findings = AnalysisFindings(
            key_insights=["insight1", "insight2"],
            contradictions=["contradiction1"],
            gaps=["gap1"],
            confidence_level=0.85,
        )

        assert len(findings.key_insights) == 2
        assert len(findings.contradictions) == 1
        assert len(findings.gaps) == 1
        assert findings.confidence_level == 0.85


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_verification_result_initialization(self):
        """Test VerificationResult initialization."""
        result = VerificationResult(
            is_verified=True,
            accuracy_score=0.90,
            completeness_score=0.85,
            consistency_score=0.95,
            issues_found=["issue1"],
            suggestions=["suggestion1"],
        )

        assert result.is_verified
        assert result.accuracy_score == 0.90
        assert result.completeness_score == 0.85
        assert result.consistency_score == 0.95
        assert len(result.issues_found) == 1
        assert len(result.suggestions) == 1
        assert isinstance(result.verified_at, datetime)