"""Tools for Hacker News agent."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from google.adk.tools import FunctionTool
from .hn_service import HackerNewsService

logger = logging.getLogger(__name__)


async def search_hacker_news(
    query: str,
    search_type: str = "story",
    num_results: int = 30
) -> str:
    """Search Hacker News for stories or comments.

    Args:
        query: Search query string
        search_type: Type to search - "story", "comment", or "all"
        num_results: Number of results to return (max 100)

    Returns:
        JSON string with search results
    """
    async with HackerNewsService() as hn_service:
        result = await hn_service.search_stories(
            query=query,
            search_type=search_type,
            num_results=num_results
        )

        response = {
            "query_type": "search",
            "search_query": query,
            "results": [
                {
                    "title": story.title,
                    "url": story.url,
                    "author": story.author,
                    "points": story.points,
                    "comments": story.num_comments,
                    "created_at": story.created_at.isoformat(),
                    "relevance": "high" if i < 5 else "medium" if i < 15 else "low"
                }
                for i, story in enumerate(result.stories)
            ],
            "metadata": {
                "total_hits": result.total_hits,
                "results_shown": len(result.stories),
                "search_time_ms": result.processing_time_ms or 0
            }
        }

        return json.dumps(response, indent=2)


async def get_trending_stories(
    time_window: str = "24h",
    min_score: int = 50
) -> str:
    """Get trending Hacker News stories based on velocity scoring.

    Args:
        time_window: Time period - "24h", "7d", or "30d"
        min_score: Minimum score threshold for stories

    Returns:
        JSON string with trending stories
    """
    async with HackerNewsService() as hn_service:
        result = await hn_service.get_trending(
            time_window=time_window,
            min_score=min_score
        )

        response = {
            "query_type": "trending",
            "time_window": time_window,
            "results": [
                {
                    "rank": i + 1,
                    "title": story.title,
                    "url": story.url,
                    "author": story.author,
                    "points": story.points,
                    "comments": story.num_comments,
                    "velocity_score": round(story.velocity, 2),
                    "created_at": story.created_at.isoformat(),
                    "summary": story.story_text[:200] if story.story_text else None
                }
                for i, story in enumerate(result.stories)
            ],
            "trending_keywords": result.trending_keywords,
            "metadata": {
                "total_stories": len(result.stories),
                "min_score": min_score,
                "generated_at": datetime.now().isoformat()
            }
        }

        return json.dumps(response, indent=2)


async def analyze_user(
    username: str,
    include_submissions: bool = True
) -> str:
    """Analyze a Hacker News user's profile and activity.

    Args:
        username: HN username to analyze
        include_submissions: Whether to include user's submissions

    Returns:
        JSON string with user analytics
    """
    async with HackerNewsService() as hn_service:
        analytics = await hn_service.get_user_analytics(
            username=username,
            include_submissions=include_submissions
        )

        if not analytics:
            return json.dumps({
                "query_type": "user",
                "error": f"User {username} not found"
            })

        response = {
            "query_type": "user",
            "username": username,
            "profile": {
                "karma": analytics.user.karma,
                "account_age_days": (datetime.now() - analytics.user.created_at).days,
                "about": analytics.user.about,
                "total_submissions": analytics.user.submission_count or 0,
                "total_comments": analytics.user.comment_count or 0
            },
            "top_stories": [
                {
                    "title": story.title,
                    "points": story.points,
                    "comments": story.num_comments,
                    "created_at": story.created_at.isoformat()
                }
                for story in analytics.top_stories
            ],
            "activity_summary": {
                "avg_story_score": round(analytics.activity_summary.get("avg_story_score", 0), 2),
                "recent_activity": analytics.recent_activity[:5]
            }
        }

        return json.dumps(response, indent=2)


async def analyze_story_comments(
    story_id: str,
    max_comments: int = 50
) -> str:
    """Analyze comments for a Hacker News story.

    Args:
        story_id: HN story ID to analyze
        max_comments: Maximum number of comments to analyze

    Returns:
        JSON string with comment analysis
    """
    async with HackerNewsService() as hn_service:
        analysis = await hn_service.analyze_comments(
            story_id=story_id,
            max_comments=max_comments
        )

        response = {
            "query_type": "comments",
            "story_id": story_id,
            "analysis": {
                "total_comments": analysis.total_comments,
                "unique_commenters": analysis.unique_commenters,
                "sentiment": {
                    "positive_ratio": round(analysis.sentiment_summary.get("positive_ratio", 0), 2),
                    "negative_ratio": round(analysis.sentiment_summary.get("negative_ratio", 0), 2),
                    "neutral_ratio": round(analysis.sentiment_summary.get("neutral_ratio", 0), 2)
                },
                "top_themes": analysis.discussion_themes,
                "sample_comments": [
                    {
                        "author": comment.author,
                        "text": comment.comment_text[:200] + "..." if len(comment.comment_text) > 200 else comment.comment_text,
                        "sentiment": "neutral"  # Would need more sophisticated analysis
                    }
                    for comment in analysis.top_comments[:5]
                ]
            }
        }

        return json.dumps(response, indent=2)


# Create Tool objects for Google ADK
# FunctionTool automatically extracts the name and description from the function docstring
search_hn_tool = FunctionTool(func=search_hacker_news)
trending_tool = FunctionTool(func=get_trending_stories)
user_tool = FunctionTool(func=analyze_user)
comments_tool = FunctionTool(func=analyze_story_comments)

# List of all available tools
HN_TOOLS = [
    search_hn_tool,
    trending_tool,
    user_tool,
    comments_tool
]