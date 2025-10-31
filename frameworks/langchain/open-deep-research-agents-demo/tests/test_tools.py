"""
Tests for Research Tools

Tests for the research tools used by agents.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock

from src.tools import (
    web_search_tool,
    summary_tool,
    analysis_tool,
    verification_tool,
    concurrent_search_tool,
    get_tool_by_name,
    get_all_tools,
)


class TestWebSearchTool:
    """Test web search tool functionality."""

    @pytest.mark.asyncio
    async def test_web_search_mock(self):
        """Test web search with mock implementation."""
        results = await web_search_tool.ainvoke({
            "query": "test query",
            "max_results": 3,
        })

        assert isinstance(results, list)
        assert len(results) <= 3
        for result in results:
            assert "url" in result
            assert "title" in result
            assert "snippet" in result
            assert "content" in result
            assert "relevance_score" in result

    @pytest.mark.asyncio
    async def test_web_search_empty_query(self):
        """Test web search with empty query."""
        results = await web_search_tool.ainvoke({
            "query": "",
            "max_results": 3,
        })

        # Should still return results (mock behavior)
        assert isinstance(results, list)


class TestSummaryTool:
    """Test summary tool functionality."""

    def test_summary_tool_basic(self):
        """Test basic summarization."""
        text = "This is a long text. " * 20 + "Important middle section. " * 5 + "Final conclusion."

        result = summary_tool.invoke({
            "text": text,
            "max_length": 100,
        })

        assert isinstance(result, str)
        assert len(result) > 0
        assert len(result.split()) <= 100

    def test_summary_tool_short_text(self):
        """Test summarization with short text."""
        text = "Short text."

        result = summary_tool.invoke({
            "text": text,
            "max_length": 100,
        })

        assert result == text

    def test_summary_tool_empty_text(self):
        """Test summarization with empty text."""
        result = summary_tool.invoke({
            "text": "",
            "max_length": 100,
        })

        assert result == "No text provided to summarize."


class TestAnalysisTool:
    """Test analysis tool functionality."""

    def test_analysis_tool_basic(self):
        """Test basic content analysis."""
        content = "This is content about technology and research with market implications."

        result = analysis_tool.invoke({
            "content": content,
            "focus_areas": ["technology", "market"],
        })

        assert isinstance(result, dict)
        assert result["success"]
        assert "insights" in result
        assert "themes" in result
        assert "statistics" in result
        assert result["statistics"]["word_count"] > 0

    def test_analysis_tool_empty_content(self):
        """Test analysis with empty content."""
        result = analysis_tool.invoke({
            "content": "",
            "focus_areas": [],
        })

        assert isinstance(result, dict)
        assert not result["success"]
        assert "error" in result

    def test_analysis_tool_with_focus_areas(self):
        """Test analysis with specific focus areas."""
        content = "Technology is advancing rapidly. Market conditions are favorable."

        result = analysis_tool.invoke({
            "content": content,
            "focus_areas": ["technology", "market"],
        })

        assert result["success"]
        assert "technology" in result["focus_areas_addressed"]
        assert "market" in result["focus_areas_addressed"]


class TestVerificationTool:
    """Test verification tool functionality."""

    def test_verification_tool_basic(self):
        """Test basic claim verification."""
        claim = "Research shows that data analysis improves outcomes."
        sources = ["source1", "source2", "source3"]

        result = verification_tool.invoke({
            "claim": claim,
            "sources": sources,
        })

        assert isinstance(result, dict)
        assert "verified" in result
        assert "confidence" in result
        assert "evidence" in result
        assert result["sources_checked"] == len(sources)

    def test_verification_tool_empty_claim(self):
        """Test verification with empty claim."""
        result = verification_tool.invoke({
            "claim": "",
            "sources": [],
        })

        assert not result["verified"]
        assert result["confidence"] == 0.0
        assert "reason" in result

    def test_verification_tool_no_sources(self):
        """Test verification without sources."""
        claim = "This is a test claim."

        result = verification_tool.invoke({
            "claim": claim,
            "sources": [],
        })

        assert isinstance(result, dict)
        assert result["sources_checked"] == 0


class TestConcurrentSearchTool:
    """Test concurrent search tool functionality."""

    @pytest.mark.asyncio
    async def test_concurrent_search(self):
        """Test concurrent search execution."""
        queries = ["query1", "query2", "query3"]

        results = await concurrent_search_tool.ainvoke({
            "queries": queries,
            "max_results_per_query": 2,
        })

        assert isinstance(results, dict)
        assert len(results) == len(queries)
        for query in queries:
            assert query in results
            assert isinstance(results[query], list)
            assert len(results[query]) <= 2

    @pytest.mark.asyncio
    async def test_concurrent_search_empty(self):
        """Test concurrent search with empty queries."""
        results = await concurrent_search_tool.ainvoke({
            "queries": [],
            "max_results_per_query": 2,
        })

        assert results == {}


class TestToolRegistry:
    """Test tool registry functions."""

    def test_get_tool_by_name(self):
        """Test getting tool by name."""
        tool = get_tool_by_name("web_search")
        assert tool is not None
        assert tool == web_search_tool

    def test_get_tool_by_name_not_found(self):
        """Test getting non-existent tool."""
        tool = get_tool_by_name("nonexistent")
        assert tool is None

    def test_get_all_tools(self):
        """Test getting all tools."""
        tools = get_all_tools()

        assert isinstance(tools, list)
        assert len(tools) == 5
        assert web_search_tool in tools
        assert summary_tool in tools
        assert analysis_tool in tools
        assert verification_tool in tools
        assert concurrent_search_tool in tools