"""Tests for Hacker News service."""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock

from src.hn_service import HackerNewsService
from src.models import HNStory, HNUser


@pytest.mark.asyncio
class TestHackerNewsService:
    """Test Hacker News service functionality."""

    async def test_search_stories(self, mock_httpx_client):
        """Test searching for stories."""
        async with HackerNewsService() as service:
            result = await service.search_stories("test query")

            assert result.query == "test query"
            assert result.total_hits == 1
            assert len(result.stories) == 1
            assert result.stories[0].title == "Test Story"

    async def test_search_with_type_filter(self, mock_httpx_client):
        """Test searching with type filter."""
        async with HackerNewsService() as service:
            # Test story search
            await service.search_stories("test", search_type="story")
            call_args = mock_httpx_client.get.call_args
            assert call_args[1]["params"]["tags"] == "story"

            # Test comment search
            await service.search_stories("test", search_type="comment")
            call_args = mock_httpx_client.get.call_args
            assert call_args[1]["params"]["tags"] == "comment"

    async def test_get_trending(self, mock_httpx_client):
        """Test getting trending stories."""
        # Mock response with multiple stories
        mock_httpx_client.get.return_value.json.return_value = {
            "hits": [
                {
                    "objectID": str(i),
                    "title": f"Story {i}",
                    "url": f"https://example.com/{i}",
                    "author": f"user{i}",
                    "points": 100 * (5 - i),  # Decreasing points
                    "num_comments": 20 * i,
                    "created_at": (datetime.now() - timedelta(hours=i)).isoformat() + "Z"
                }
                for i in range(1, 6)
            ],
            "nbHits": 5
        }

        async with HackerNewsService(max_stories=3) as service:
            result = await service.get_trending(time_window="24h", min_score=50)

            assert result.time_window == "24h"
            assert len(result.stories) <= 3
            assert len(result.trending_keywords) > 0

            # Check stories are sorted by velocity
            velocities = [story.velocity for story in result.stories]
            assert velocities == sorted(velocities, reverse=True)

    async def test_get_user_analytics(self, mock_httpx_client):
        """Test getting user analytics."""
        # Mock user profile response
        user_response = MagicMock()
        user_response.json.return_value = {
            "username": "testuser",
            "created_at_i": 1600000000,
            "karma": 5000,
            "about": "Test bio",
            "submission_count": 100,
            "comment_count": 500
        }
        user_response.raise_for_status = MagicMock()

        # Mock user stories response
        stories_response = MagicMock()
        stories_response.json.return_value = {
            "hits": [
                {
                    "objectID": "1",
                    "title": "User Story",
                    "url": "https://example.com",
                    "points": 200,
                    "num_comments": 50,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ]
        }
        stories_response.raise_for_status = MagicMock()

        # Configure mock to return different responses
        mock_httpx_client.get.side_effect = [user_response, stories_response, stories_response]

        async with HackerNewsService() as service:
            result = await service.get_user_analytics("testuser")

            assert result is not None
            assert result.user.username == "testuser"
            assert result.user.karma == 5000
            assert len(result.top_stories) > 0
            assert "total_karma" in result.activity_summary

    async def test_analyze_comments(self, mock_httpx_client):
        """Test analyzing story comments."""
        # Mock comments response
        mock_httpx_client.get.return_value.json.return_value = {
            "hits": [
                {
                    "objectID": f"comment{i}",
                    "author": f"user{i}",
                    "comment_text": f"This is a great story! Comment {i}",
                    "created_at": "2024-01-01T00:00:00Z",
                    "parent_id": "12345",
                    "points": 10
                }
                for i in range(1, 6)
            ],
            "nbHits": 10
        }

        async with HackerNewsService() as service:
            result = await service.analyze_comments("12345", max_comments=5)

            assert result.story_id == "12345"
            assert result.total_comments == 10
            assert result.unique_commenters == 5
            assert len(result.top_comments) == 5
            assert "positive_ratio" in result.sentiment_summary
            assert len(result.discussion_themes) > 0

    async def test_extract_trending_keywords(self):
        """Test keyword extraction from text."""
        service = HackerNewsService()
        texts = [
            "Python programming is amazing for machine learning",
            "JavaScript and React are popular for web development",
            "Machine learning with Python is powerful"
        ]

        keywords = service._extract_trending_keywords(texts, num_keywords=5)

        assert "python" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert len(keywords) <= 5

    async def test_error_handling(self, mock_httpx_client):
        """Test error handling in service methods."""
        # Configure mock to raise exception
        mock_httpx_client.get.side_effect = Exception("API Error")

        async with HackerNewsService() as service:
            # Test search error handling
            result = await service.search_stories("test")
            assert result.total_hits == 0
            assert len(result.stories) == 0

            # Test trending error handling
            trending = await service.get_trending()
            assert len(trending.stories) == 0

            # Test user analytics error handling
            user = await service.get_user_analytics("testuser")
            assert user is None

            # Test comments error handling
            comments = await service.analyze_comments("12345")
            assert comments.total_comments == 0

    async def test_context_manager(self):
        """Test service as async context manager."""
        async with HackerNewsService() as service:
            assert service.client is not None
            assert service.max_stories == 30
            assert service.search_limit == 100

        # After exiting, client should be closed
        # (In real implementation, would verify client.aclose() was called)