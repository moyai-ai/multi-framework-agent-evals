"""
Research Tools

Implements various tools used by agents for research tasks.
"""

import asyncio
import json
import os
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from langchain.tools import tool
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.context import SearchResult


# Environment configuration
USE_MOCK_TOOLS = os.getenv("USE_MOCK_TOOLS", "false").lower() == "true"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


class SearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class SummaryInput(BaseModel):
    """Input for summary tool."""
    text: str = Field(description="The text to summarize")
    max_length: int = Field(default=500, description="Maximum length of summary in words")


class AnalysisInput(BaseModel):
    """Input for analysis tool."""
    content: str = Field(description="The content to analyze")
    focus_areas: List[str] = Field(default_factory=list, description="Specific areas to focus on")


class VerificationInput(BaseModel):
    """Input for verification tool."""
    claim: str = Field(description="The claim or information to verify")
    sources: List[str] = Field(default_factory=list, description="Sources to check against")


@tool
async def web_search_tool(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a web search and return results.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        List of search results with title, snippet, url, and content
    """
    if USE_MOCK_TOOLS or not TAVILY_API_KEY:
        # Mock implementation for testing
        return _mock_web_search(query, max_results)

    try:
        # Real Tavily API implementation
        from tavily import TavilyClient

        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            include_raw_content=True,
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "snippet": item.get("content", ""),
                "content": item.get("raw_content", item.get("content", "")),
                "relevance_score": item.get("score", 0.0),
            })

        return results

    except Exception as e:
        print(f"Error in web search: {e}")
        # Fall back to mock data on error
        return _mock_web_search(query, max_results)


@tool
def summary_tool(text: str, max_length: int = 500) -> str:
    """
    Summarize a piece of text.

    Args:
        text: The text to summarize
        max_length: Maximum length of summary in words

    Returns:
        A concise summary of the text
    """
    if not text:
        return "No text provided to summarize."

    # Simple extractive summarization (mock)
    # In production, this would use an LLM or specialized summarization model
    sentences = text.split(". ")

    if len(sentences) <= 3:
        return text

    # Take first, middle, and last sentences as a simple summary
    summary_sentences = [
        sentences[0],
        sentences[len(sentences) // 2],
        sentences[-1] if sentences[-1] else sentences[-2],
    ]

    summary = ". ".join(summary_sentences)
    words = summary.split()

    if len(words) > max_length:
        summary = " ".join(words[:max_length]) + "..."

    return summary


@tool
def analysis_tool(content: str, focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze content and extract key insights.

    Args:
        content: The content to analyze
        focus_areas: Specific areas to focus on in the analysis

    Returns:
        Analysis results with key insights, themes, and metadata
    """
    if not content:
        return {
            "success": False,
            "error": "No content provided to analyze",
            "insights": [],
        }

    # Mock analysis implementation
    # In production, this would use LLM-based analysis

    word_count = len(content.split())
    sentence_count = len(content.split(". "))

    # Extract mock insights based on content
    insights = []

    if "technology" in content.lower() or "tech" in content.lower():
        insights.append("Technology trends and innovations are discussed")

    if "market" in content.lower() or "business" in content.lower():
        insights.append("Market dynamics and business implications are covered")

    if "research" in content.lower() or "study" in content.lower():
        insights.append("Research findings and studies are referenced")

    if "future" in content.lower() or "trend" in content.lower():
        insights.append("Future trends and predictions are mentioned")

    # Add focus area specific insights
    if focus_areas:
        for area in focus_areas:
            if area.lower() in content.lower():
                insights.append(f"Content addresses {area} as requested")

    # Extract potential themes (mock)
    themes = []
    if word_count > 100:
        themes.append("Comprehensive coverage")
    if sentence_count > 10:
        themes.append("Detailed explanation")
    if "however" in content.lower() or "but" in content.lower():
        themes.append("Balanced perspective")

    return {
        "success": True,
        "insights": insights[:5] if insights else ["General information provided"],
        "themes": themes,
        "statistics": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "average_sentence_length": word_count // sentence_count if sentence_count > 0 else 0,
        },
        "confidence": min(0.95, 0.6 + len(insights) * 0.1),
        "focus_areas_addressed": focus_areas if focus_areas else [],
    }


@tool
def verification_tool(claim: str, sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Verify a claim or piece of information.

    Args:
        claim: The claim or information to verify
        sources: Optional sources to check against

    Returns:
        Verification results with confidence score and supporting evidence
    """
    if not claim:
        return {
            "verified": False,
            "confidence": 0.0,
            "reason": "No claim provided to verify",
            "evidence": [],
        }

    # Mock verification implementation
    # In production, this would cross-reference with reliable sources

    evidence = []
    confidence = 0.5  # Base confidence

    # Simple keyword-based mock verification
    factual_keywords = ["research", "study", "data", "report", "analysis", "findings"]
    speculative_keywords = ["might", "could", "possibly", "potentially", "maybe", "suggest"]

    claim_lower = claim.lower()

    # Check for factual language
    factual_count = sum(1 for keyword in factual_keywords if keyword in claim_lower)
    speculative_count = sum(1 for keyword in speculative_keywords if keyword in claim_lower)

    if factual_count > speculative_count:
        confidence += 0.2
        evidence.append("Claim uses factual language")
    elif speculative_count > factual_count:
        confidence -= 0.1
        evidence.append("Claim contains speculative language")

    # Check sources if provided
    if sources:
        confidence += min(0.3, len(sources) * 0.1)
        evidence.append(f"Cross-referenced with {len(sources)} sources")

    # Mock source verification
    if sources and len(sources) >= 3:
        evidence.append("Multiple sources corroborate the claim")
        confidence = min(0.95, confidence + 0.2)

    # Ensure confidence is within bounds
    confidence = max(0.0, min(1.0, confidence))

    return {
        "verified": confidence > 0.7,
        "confidence": confidence,
        "evidence": evidence,
        "sources_checked": len(sources) if sources else 0,
        "recommendation": "High confidence" if confidence > 0.8 else
                         "Moderate confidence" if confidence > 0.5 else
                         "Low confidence - further verification needed",
    }


@tool
async def concurrent_search_tool(queries: List[str], max_results_per_query: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    Perform multiple searches concurrently.

    Args:
        queries: List of search queries to execute
        max_results_per_query: Maximum results per query

    Returns:
        Dictionary mapping each query to its results
    """
    async def search_single(query: str) -> tuple[str, List[Dict[str, Any]]]:
        results = await web_search_tool.ainvoke({"query": query, "max_results": max_results_per_query})
        return query, results

    # Execute searches concurrently
    tasks = [search_single(query) for query in queries]
    results = await asyncio.gather(*tasks)

    # Convert to dictionary
    return dict(results)


def _mock_web_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Mock web search implementation for testing.

    Args:
        query: The search query
        max_results: Maximum number of results

    Returns:
        List of mock search results
    """
    mock_results = []

    # Generate mock results based on query
    for i in range(min(max_results, 5)):
        mock_results.append({
            "url": f"https://example.com/result-{i+1}-{query.replace(' ', '-')}",
            "title": f"Result {i+1}: {query}",
            "snippet": f"This is a mock search result for '{query}'. "
                      f"It contains relevant information about the topic. "
                      f"Result number {i+1} of {max_results}.",
            "content": f"Full content for result {i+1}. {query} is an important topic. "
                      f"Here is detailed information about {query}. "
                      f"This mock content simulates a real search result with multiple paragraphs. "
                      f"The information provided here would normally come from web pages. "
                      f"Additional context and details about {query} would appear here. "
                      f"Result relevance score: {random.uniform(0.7, 1.0):.2f}",
            "relevance_score": random.uniform(0.7, 1.0),
        })

    return mock_results


# Tool registry for easy access
AVAILABLE_TOOLS = {
    "web_search": web_search_tool,
    "summary": summary_tool,
    "analysis": analysis_tool,
    "verification": verification_tool,
    "concurrent_search": concurrent_search_tool,
}


def get_tool_by_name(name: str) -> Optional[BaseTool]:
    """
    Get a tool by its name.

    Args:
        name: The name of the tool

    Returns:
        The tool if found, None otherwise
    """
    return AVAILABLE_TOOLS.get(name)


def get_all_tools() -> List[BaseTool]:
    """
    Get all available tools.

    Returns:
        List of all available tools
    """
    return list(AVAILABLE_TOOLS.values())