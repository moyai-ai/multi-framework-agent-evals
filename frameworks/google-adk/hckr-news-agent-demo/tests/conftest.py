"""Pytest configuration and fixtures for Hacker News agent tests."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.models import HNStory, HNComment, HNUser


@pytest.fixture
def mock_hn_service():
    """Mock Hacker News service."""
    service = AsyncMock()

    # Mock search results
    service.search_stories = AsyncMock(return_value=MagicMock(
        query="test",
        total_hits=100,
        stories=[
            HNStory(
                objectID="1",
                title="Test Story 1",
                url="https://example.com/1",
                author="user1",
                points=150,
                num_comments=45,
                created_at=datetime.now()
            ),
            HNStory(
                objectID="2",
                title="Test Story 2",
                url="https://example.com/2",
                author="user2",
                points=200,
                num_comments=60,
                created_at=datetime.now()
            )
        ],
        processing_time_ms=50
    ))

    # Mock trending results
    service.get_trending = AsyncMock(return_value=MagicMock(
        time_window="24h",
        stories=[
            HNStory(
                objectID="3",
                title="Trending Story",
                url="https://trending.com",
                author="trendy",
                points=500,
                num_comments=150,
                created_at=datetime.now()
            )
        ],
        trending_keywords=["ai", "python", "startup"]
    ))

    # Mock user analytics
    service.get_user_analytics = AsyncMock(return_value=MagicMock(
        user=HNUser(
            username="testuser",
            created_at=datetime(2020, 1, 1),
            karma=5000,
            about="Test user bio"
        ),
        top_stories=[],
        recent_activity=[],
        activity_summary={"total_karma": 5000}
    ))

    # Mock comment analysis
    service.analyze_comments = AsyncMock(return_value=MagicMock(
        story_id="12345",
        total_comments=50,
        unique_commenters=25,
        top_comments=[],
        sentiment_summary={"positive_ratio": 0.6, "negative_ratio": 0.2, "neutral_ratio": 0.2},
        discussion_themes=["technology", "innovation"]
    ))

    return service


@pytest.fixture
def sample_qa_pairs():
    """Sample Q&A pairs for testing HN agent."""
    return {
        "trending": "What are the trending stories on Hacker News?",
        "search": "Search for stories about artificial intelligence",
        "user": "Tell me about user pg on Hacker News",
        "comments": "Analyze the comments for story 12345"
    }


@pytest.fixture
def api_key():
    """Check if Google API key is available."""
    return os.environ.get("GOOGLE_API_KEY")


@pytest.fixture
def skip_if_no_api_key(api_key):
    """Skip test if no API key is available."""
    if not api_key:
        pytest.skip("No Google API key found in environment")


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        client_instance = AsyncMock()

        # Add aclose method as AsyncMock
        client_instance.aclose = AsyncMock()

        # Mock Algolia API responses
        client_instance.get = AsyncMock(return_value=MagicMock(
            raise_for_status=MagicMock(),
            json=MagicMock(return_value={
                "hits": [
                    {
                        "objectID": "1",
                        "title": "Test Story",
                        "url": "https://test.com",
                        "author": "testuser",
                        "points": 100,
                        "num_comments": 20,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "nbHits": 1,
                "processingTimeMS": 10
            })
        ))

        # Return the mock instance directly when AsyncClient is instantiated
        mock_client.return_value = client_instance

        yield client_instance


@pytest.fixture
def sample_story():
    """Sample HN story for testing."""
    return HNStory(
        objectID="test123",
        title="Sample Hacker News Story",
        url="https://example.com/story",
        author="sampleuser",
        points=250,
        num_comments=75,
        created_at=datetime.now(),
        story_text="This is a sample story text for testing."
    )


@pytest.fixture
def sample_comment():
    """Sample HN comment for testing."""
    return HNComment(
        objectID="comment123",
        author="commenter",
        comment_text="This is a sample comment for testing purposes.",
        created_at=datetime.now(),
        parent_id="test123",
        story_id="test123",
        points=10
    )


@pytest.fixture
def sample_user():
    """Sample HN user for testing."""
    return HNUser(
        username="sampleuser",
        created_at=datetime(2020, 6, 15),
        karma=1500,
        about="Sample user bio for testing.",
        submission_count=50,
        comment_count=200
    )