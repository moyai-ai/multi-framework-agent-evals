"""
Tests for Research Agents

Comprehensive test suite for research agents and their components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.agents import (
    PlannerAgent,
    SearchAgent,
    AnalystAgent,
    SummarizerAgent,
    WriterAgent,
    VerifierAgent,
    get_agent_by_name,
    list_agents,
)
from src.context import WorkflowStage, SearchResult


class TestAgentRegistry:
    """Test agent registry functions."""

    def test_get_agent_by_name_exact(self):
        """Test getting agent by exact name."""
        agent = get_agent_by_name("planner")
        assert agent is not None
        assert isinstance(agent, PlannerAgent)

    def test_get_agent_by_name_case_insensitive(self):
        """Test getting agent by name with different case."""
        agent = get_agent_by_name("PLANNER")
        assert agent is not None
        assert isinstance(agent, PlannerAgent)

    def test_get_agent_by_name_not_found(self):
        """Test getting non-existent agent."""
        agent = get_agent_by_name("nonexistent")
        assert agent is None

    def test_list_agents(self):
        """Test listing all agents."""
        agents = list_agents()
        assert len(agents) == 6
        expected_agents = ["planner", "search", "analyst", "summarizer", "writer", "verifier"]
        for agent_name in expected_agents:
            assert agent_name in agents


class TestPlannerAgent:
    """Test PlannerAgent functionality."""

    @pytest.mark.asyncio
    async def test_create_search_plan(self, sample_context):
        """Test creating a search plan."""
        planner = PlannerAgent()

        # Mock the execute method to return a controlled response
        with patch.object(planner, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
                Search Terms:
                1. latest AI developments 2024
                2. artificial intelligence breakthroughs
                3. recent machine learning advances

                Strategy: Comprehensive search across multiple dimensions
                """,
            }

            plan = await planner.create_search_plan(sample_context)

            assert plan is not None
            assert len(plan.search_terms) > 0
            assert plan.search_strategy != ""
            assert plan.max_results_per_term == 5

    @pytest.mark.asyncio
    async def test_create_search_plan_fallback(self, sample_context):
        """Test search plan creation with fallback on error."""
        planner = PlannerAgent()

        # Mock execute to simulate failure
        with patch.object(planner, "execute") as mock_execute:
            mock_execute.return_value = {"success": False, "error": "API error"}

            plan = await planner.create_search_plan(sample_context)

            assert plan is not None
            assert len(plan.search_terms) >= 3
            assert sample_context.query in plan.search_terms[0]


class TestSearchAgent:
    """Test SearchAgent functionality."""

    @pytest.mark.asyncio
    async def test_conduct_searches(self, context_with_results):
        """Test conducting searches."""
        searcher = SearchAgent()

        # Mock the execute method
        with patch.object(searcher, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": "Search completed",
                "intermediate_steps": [],
            }

            results = await searcher.conduct_searches(context_with_results)

            assert isinstance(results, dict)
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_conduct_searches_no_plan(self, sample_context):
        """Test conducting searches without a search plan."""
        searcher = SearchAgent()
        results = await searcher.conduct_searches(sample_context)

        assert results == {}


class TestAnalystAgent:
    """Test AnalystAgent functionality."""

    @pytest.mark.asyncio
    async def test_analyze_results(self, context_with_results):
        """Test analyzing search results."""
        analyst = AnalystAgent()

        # Mock the execute method
        with patch.object(analyst, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
                Key Insights:
                - AI is advancing rapidly
                - Machine learning is becoming more efficient

                Contradictions:
                - Some experts disagree on timeline

                Gaps:
                - Limited long-term data
                """,
            }

            findings = await analyst.analyze_results(context_with_results)

            assert findings is not None
            assert len(findings.key_insights) > 0
            assert findings.confidence_level > 0

    @pytest.mark.asyncio
    async def test_analyze_empty_results(self, sample_context):
        """Test analyzing with no search results."""
        analyst = AnalystAgent()
        findings = await analyst.analyze_results(sample_context)

        assert findings is not None
        assert findings.confidence_level == 0.0


class TestSummarizerAgent:
    """Test SummarizerAgent functionality."""

    @pytest.mark.asyncio
    async def test_create_summaries(self, context_with_results, sample_analysis):
        """Test creating summaries."""
        context_with_results.analysis_findings = sample_analysis
        summarizer = SummarizerAgent()

        # Mock the execute method
        with patch.object(summarizer, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": "Executive Summary: AI is advancing rapidly.",
            }

            summaries = await summarizer.create_summaries(context_with_results)

            assert len(summaries) > 0
            assert summaries[0] != ""

    @pytest.mark.asyncio
    async def test_create_summaries_no_analysis(self, sample_context):
        """Test creating summaries without analysis."""
        summarizer = SummarizerAgent()
        summaries = await summarizer.create_summaries(sample_context)

        assert summaries == []


class TestWriterAgent:
    """Test WriterAgent functionality."""

    @pytest.mark.asyncio
    async def test_write_report(self, complete_context):
        """Test writing a research report."""
        writer = WriterAgent()

        # Mock the execute method
        with patch.object(writer, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
## Executive Summary
Comprehensive research on AI developments.

## Key Findings
- Finding 1
- Finding 2

## Sources
1. Source 1
2. Source 2
                """,
            }

            report = await writer.write_report(complete_context)

            assert report is not None
            assert len(report) > 0
            assert "Executive Summary" in report


class TestVerifierAgent:
    """Test VerifierAgent functionality."""

    @pytest.mark.asyncio
    async def test_verify_research(self, complete_context):
        """Test verifying research quality."""
        verifier = VerifierAgent()

        # Mock the execute method
        with patch.object(verifier, "execute") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "output": """
                Verification complete:
                - Accuracy: High
                - Completeness: Good
                - Consistency: Excellent

                Issues: Minor formatting issue

                Suggestions: Add more recent sources
                """,
            }

            verification = await verifier.verify_research(complete_context)

            assert verification is not None
            assert verification.is_verified
            assert verification.accuracy_score > 0

    @pytest.mark.asyncio
    async def test_verify_research_failure(self, complete_context):
        """Test verification with failure."""
        verifier = VerifierAgent()

        # Mock execute to simulate failure
        with patch.object(verifier, "execute") as mock_execute:
            mock_execute.return_value = {"success": False, "error": "Verification failed"}

            verification = await verifier.verify_research(complete_context)

            assert verification is not None
            assert not verification.is_verified