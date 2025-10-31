"""
Tests for Research Manager

Tests for the research orchestration manager.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, Mock

from src.manager import ResearchManager
from src.context import ResearchContext, WorkflowStage, ResearchType


class TestResearchManager:
    """Test ResearchManager functionality."""

    @pytest.mark.asyncio
    async def test_conduct_research_complete_workflow(self):
        """Test complete research workflow execution."""
        manager = ResearchManager(verbose=False)

        # Mock all agent methods
        with patch.object(manager, "_planning_stage", new_callable=AsyncMock) as mock_planning, \
             patch.object(manager, "_searching_stage", new_callable=AsyncMock) as mock_searching, \
             patch.object(manager, "_analysis_stage", new_callable=AsyncMock) as mock_analysis, \
             patch.object(manager, "_summarization_stage", new_callable=AsyncMock) as mock_summary, \
             patch.object(manager, "_writing_stage", new_callable=AsyncMock) as mock_writing, \
             patch.object(manager, "_verification_stage", new_callable=AsyncMock) as mock_verify:

            query = "Test research query"
            context = await manager.conduct_research(query)

            # Check all stages were called
            mock_planning.assert_called_once()
            mock_searching.assert_called_once()
            mock_analysis.assert_called_once()
            mock_summary.assert_called_once()
            mock_writing.assert_called_once()
            mock_verify.assert_called_once()

            # Check context state
            assert context.query == query
            assert context.current_stage == WorkflowStage.COMPLETE
            assert context.is_complete()

    @pytest.mark.asyncio
    async def test_conduct_research_with_error(self):
        """Test research workflow with error handling."""
        manager = ResearchManager(verbose=False)

        # Mock planning stage to raise an error
        with patch.object(manager, "_planning_stage") as mock_planning:
            mock_planning.side_effect = Exception("Planning error")

            query = "Test research query"
            context = await manager.conduct_research(query)

            # Check error handling
            assert context.current_stage == WorkflowStage.ERROR
            assert context.is_complete()
            assert len(context.errors) > 0
            assert "Planning error" in context.errors[0]

    @pytest.mark.asyncio
    async def test_planning_stage(self, sample_context, sample_search_plan):
        """Test planning stage execution."""
        manager = ResearchManager(verbose=False)

        # Mock planner agent
        mock_planner = Mock()
        mock_planner.create_search_plan = AsyncMock(return_value=sample_search_plan)
        manager.agents["planner"] = mock_planner

        await manager._planning_stage(sample_context)

        assert sample_context.current_stage == WorkflowStage.PLANNING
        assert sample_context.search_plan == sample_search_plan
        mock_planner.create_search_plan.assert_called_once_with(sample_context)

    @pytest.mark.asyncio
    async def test_searching_stage(self, sample_context, sample_search_plan, sample_search_results):
        """Test searching stage execution."""
        manager = ResearchManager(verbose=False)
        sample_context.search_plan = sample_search_plan

        # Mock search agent
        mock_searcher = Mock()
        mock_searcher.conduct_searches = AsyncMock(return_value={
            "term1": sample_search_results[:2],
            "term2": sample_search_results[2:],
        })
        manager.agents["search"] = mock_searcher

        await manager._searching_stage(sample_context)

        assert sample_context.current_stage == WorkflowStage.SEARCHING
        assert sample_context.total_results_collected > 0
        assert sample_context.search_iterations > 0

    @pytest.mark.asyncio
    async def test_analysis_stage(self, context_with_results, sample_analysis):
        """Test analysis stage execution."""
        manager = ResearchManager(verbose=False)

        # Mock analyst agent
        mock_analyst = Mock()
        mock_analyst.analyze_results = AsyncMock(return_value=sample_analysis)
        manager.agents["analyst"] = mock_analyst

        await manager._analysis_stage(context_with_results)

        assert context_with_results.current_stage == WorkflowStage.ANALYZING
        assert context_with_results.analysis_findings == sample_analysis
        mock_analyst.analyze_results.assert_called_once_with(context_with_results)

    @pytest.mark.asyncio
    async def test_summarization_stage(self, context_with_results, sample_analysis):
        """Test summarization stage execution."""
        manager = ResearchManager(verbose=False)
        context_with_results.analysis_findings = sample_analysis

        # Mock summarizer agent
        mock_summarizer = Mock()
        mock_summarizer.create_summaries = AsyncMock(return_value=["Summary text"])
        manager.agents["summarizer"] = mock_summarizer

        await manager._summarization_stage(context_with_results)

        assert context_with_results.current_stage == WorkflowStage.SUMMARIZING
        assert len(context_with_results.raw_summaries) > 0
        assert context_with_results.executive_summary != ""

    @pytest.mark.asyncio
    async def test_writing_stage(self, context_with_results, sample_analysis):
        """Test writing stage execution."""
        manager = ResearchManager(verbose=False)
        context_with_results.analysis_findings = sample_analysis
        context_with_results.raw_summaries = ["Summary"]

        # Mock writer agent
        mock_writer = Mock()
        report = "## Executive Summary\nTest report\n## Key Findings\nFindings here"
        mock_writer.write_report = AsyncMock(return_value=report)
        manager.agents["writer"] = mock_writer

        await manager._writing_stage(context_with_results)

        assert context_with_results.current_stage == WorkflowStage.WRITING
        assert context_with_results.full_report == report
        assert len(context_with_results.report_sections) > 0

    @pytest.mark.asyncio
    async def test_verification_stage(self, complete_context, sample_verification):
        """Test verification stage execution."""
        manager = ResearchManager(verbose=False)

        # Mock verifier agent
        mock_verifier = Mock()
        mock_verifier.verify_research = AsyncMock(return_value=sample_verification)
        manager.agents["verifier"] = mock_verifier

        await manager._verification_stage(complete_context)

        assert complete_context.current_stage == WorkflowStage.VERIFYING
        assert complete_context.verification_result == sample_verification
        mock_verifier.verify_research.assert_called_once_with(complete_context)

    def test_log_verbose_mode(self, capsys):
        """Test logging in verbose mode."""
        manager = ResearchManager(verbose=True)
        manager._log("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_log_quiet_mode(self, capsys):
        """Test logging in quiet mode."""
        manager = ResearchManager(verbose=False)
        manager._log("Test message")

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_summary(self, complete_context, capsys):
        """Test printing research summary."""
        manager = ResearchManager(verbose=True)
        manager._print_summary(complete_context)

        captured = capsys.readouterr()
        assert "RESEARCH SUMMARY" in captured.out
        assert complete_context.query in captured.out