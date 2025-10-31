"""
Test Configuration and Fixtures

Provides pytest fixtures for testing research agents.
"""

import os
import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Set environment variables for testing
os.environ["USE_MOCK_TOOLS"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["VERBOSE"] = "false"

from src.context import (
    ResearchContext,
    ResearchType,
    WorkflowStage,
    SearchPlan,
    SearchResult,
    AnalysisFindings,
    ReportSection,
    VerificationResult,
)
from src.manager import ResearchManager
from src.runner import ScenarioRunner


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_context():
    """Create a sample research context for testing."""
    return ResearchContext(
        query="What are the latest developments in artificial intelligence?",
        research_type=ResearchType.TECHNICAL,
        user_requirements={"depth": "comprehensive", "focus": "recent"},
    )


@pytest.fixture
def sample_search_plan():
    """Create a sample search plan."""
    return SearchPlan(
        search_terms=[
            "latest AI developments 2024",
            "artificial intelligence breakthroughs",
            "recent machine learning advances",
            "AI technology trends",
        ],
        search_strategy="Comprehensive search covering recent developments, breakthroughs, and trends",
        max_results_per_term=5,
    )


@pytest.fixture
def sample_search_results():
    """Create sample search results."""
    return [
        SearchResult(
            url="https://example.com/ai-news-1",
            title="Major AI Breakthrough in 2024",
            snippet="Researchers announce significant advancement in AI technology...",
            content="Full article content about AI breakthrough...",
            relevance_score=0.95,
        ),
        SearchResult(
            url="https://example.com/ai-news-2",
            title="Machine Learning Advances",
            snippet="New techniques in machine learning show promise...",
            content="Detailed content about ML advances...",
            relevance_score=0.88,
        ),
        SearchResult(
            url="https://example.com/ai-trends",
            title="AI Trends for 2024",
            snippet="Key trends shaping the AI landscape this year...",
            content="Comprehensive analysis of AI trends...",
            relevance_score=0.92,
        ),
    ]


@pytest.fixture
def sample_analysis():
    """Create sample analysis findings."""
    return AnalysisFindings(
        key_insights=[
            "AI capabilities are advancing rapidly in 2024",
            "Machine learning models are becoming more efficient",
            "Ethical AI considerations are gaining prominence",
        ],
        supporting_evidence=[
            {"type": "research", "content": "Multiple studies confirm rapid progress"},
            {"type": "industry", "content": "Major companies investing heavily in AI"},
        ],
        contradictions=["Some experts caution about AI risks"],
        gaps=["Limited information on long-term impacts"],
        confidence_level=0.85,
    )


@pytest.fixture
def sample_verification():
    """Create sample verification results."""
    return VerificationResult(
        is_verified=True,
        accuracy_score=0.90,
        completeness_score=0.85,
        consistency_score=0.92,
        issues_found=["Minor inconsistency in timeline"],
        suggestions=["Add more recent sources", "Clarify technical terms"],
    )


@pytest.fixture
def sample_scenario():
    """Create a sample research scenario."""
    return {
        "name": "AI Development Research",
        "description": "Research latest developments in artificial intelligence",
        "query": "What are the latest developments in artificial intelligence?",
        "expectations": {
            "min_search_terms": 3,
            "min_report_length": 500,
            "required_sections": ["Key Findings", "Sources"],
            "verification_should_pass": True,
            "required_keywords": ["AI", "machine learning", "technology"],
        },
        "metadata": {
            "research_type": "technical",
            "priority": "high",
            "test_type": "comprehensive",
        },
    }


@pytest.fixture
def scenario_runner():
    """Create a scenario runner for testing."""
    return ScenarioRunner(verbose=False)


@pytest.fixture
def research_manager():
    """Create a research manager for testing."""
    return ResearchManager(verbose=False)


@pytest.fixture
def performance_thresholds():
    """Define performance thresholds for testing."""
    return {
        "max_planning_time": 10.0,  # seconds
        "max_search_time": 30.0,
        "max_analysis_time": 20.0,
        "max_writing_time": 25.0,
        "max_total_time": 120.0,
        "min_search_results": 5,
        "min_report_length": 500,
    }


@pytest.fixture
def mock_api_keys():
    """Provide mock API keys for testing."""
    return {
        "openai": "test-openai-key",
        "tavily": "test-tavily-key",
    }


@pytest.fixture
def sample_scenarios_list():
    """Create a list of diverse test scenarios."""
    return [
        {
            "name": "Technology Research",
            "query": "Latest developments in quantum computing",
            "research_type": "technical",
            "expectations": {
                "min_search_terms": 3,
                "min_report_length": 400,
            },
        },
        {
            "name": "Market Analysis",
            "query": "Electric vehicle market trends 2024",
            "research_type": "market",
            "expectations": {
                "min_search_terms": 4,
                "required_keywords": ["market", "trends", "electric"],
            },
        },
        {
            "name": "Scientific Study",
            "query": "Recent discoveries in gene editing",
            "research_type": "scientific",
            "expectations": {
                "min_search_terms": 3,
                "verification_should_pass": True,
            },
        },
    ]


@pytest.fixture
def context_with_results(sample_context, sample_search_plan, sample_search_results):
    """Create a context with search results populated."""
    context = sample_context
    context.search_plan = sample_search_plan
    context.transition_to(WorkflowStage.SEARCHING)

    # Add search results
    for term in sample_search_plan.search_terms[:2]:
        context.add_search_results(term, sample_search_results)

    return context


@pytest.fixture
def complete_context(context_with_results, sample_analysis, sample_verification):
    """Create a fully completed research context."""
    context = context_with_results

    # Add analysis
    context.transition_to(WorkflowStage.ANALYZING)
    context.analysis_findings = sample_analysis

    # Add summaries
    context.transition_to(WorkflowStage.SUMMARIZING)
    context.raw_summaries = [
        "This research explores the latest developments in AI technology."
    ]
    context.executive_summary = "AI is advancing rapidly with significant breakthroughs."

    # Add report
    context.transition_to(WorkflowStage.WRITING)
    context.full_report = """
## Executive Summary
AI is advancing rapidly with significant breakthroughs.

## Key Findings
- AI capabilities are advancing rapidly
- Machine learning models are becoming more efficient
- Ethical considerations are gaining prominence

## Sources
1. Major AI Breakthrough in 2024
2. Machine Learning Advances
3. AI Trends for 2024
"""

    # Add verification
    context.transition_to(WorkflowStage.VERIFYING)
    context.verification_result = sample_verification

    # Mark complete
    context.transition_to(WorkflowStage.COMPLETE)

    return context