"""Hacker News service using Algolia Search API (no authentication required)."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
from collections import Counter
import re

from .models import (
    HNStory,
    HNComment,
    HNUser,
    HNSearchResult,
    HNTrendingResult,
    HNUserAnalytics,
    HNCommentAnalysis
)

logger = logging.getLogger(__name__)


class HackerNewsService:
    """Service for interacting with Hacker News via Algolia API."""

    BASE_URL = "https://hn.algolia.com/api/v1"

    def __init__(self, max_stories: int = 30, search_limit: int = 100):
        """Initialize the HN service.

        Args:
            max_stories: Maximum number of stories to return in trending/search
            search_limit: Maximum results per API call
        """
        self.max_stories = max_stories
        self.search_limit = search_limit
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_stories(
        self,
        query: str,
        search_type: str = "story",
        num_results: int = None
    ) -> HNSearchResult:
        """Search Hacker News stories.

        Args:
            query: Search query string
            search_type: Type of content to search ("story", "comment", "all")
            num_results: Number of results to return

        Returns:
            HNSearchResult with matching stories
        """
        num_results = num_results or self.max_stories

        params = {
            "query": query,
            "hitsPerPage": min(num_results, self.search_limit)
        }

        if search_type != "all":
            params["tags"] = search_type

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            stories = []
            for hit in data.get("hits", [])[:num_results]:
                if hit.get("title"):  # Only include items with titles (stories)
                    story = HNStory(
                        objectID=hit.get("objectID", ""),
                        title=hit.get("title", ""),
                        url=hit.get("url"),
                        author=hit.get("author", "unknown"),
                        points=hit.get("points", 0),
                        num_comments=hit.get("num_comments", 0),
                        created_at=datetime.fromisoformat(
                            hit.get("created_at", datetime.now().isoformat()).replace("Z", "+00:00")
                        ),
                        story_text=hit.get("story_text")
                    )
                    stories.append(story)

            return HNSearchResult(
                query=query,
                total_hits=data.get("nbHits", 0),
                stories=stories,
                processing_time_ms=data.get("processingTimeMS")
            )

        except Exception as e:
            logger.error(f"Error searching stories: {e}")
            return HNSearchResult(query=query, total_hits=0, stories=[])

    async def get_trending(
        self,
        time_window: str = "24h",
        min_score: int = 50
    ) -> HNTrendingResult:
        """Get trending stories based on velocity (points/age).

        Args:
            time_window: Time window ("24h", "7d", "30d")
            min_score: Minimum score threshold

        Returns:
            HNTrendingResult with trending stories and keywords
        """
        # Convert time window to timedelta
        time_map = {
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        delta = time_map.get(time_window, timedelta(hours=24))

        # Calculate timestamp for filtering (use UTC to avoid timezone issues)
        from datetime import timezone
        since_timestamp = int((datetime.now(timezone.utc) - delta).timestamp())

        params = {
            "tags": "story",
            "numericFilters": [
                f"created_at_i>{since_timestamp}",
                f"points>{min_score}"
            ],
            "hitsPerPage": 100  # Get more to sort by velocity
        }

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/search_by_date",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            stories = []
            for hit in data.get("hits", []):
                if hit.get("title"):
                    story = HNStory(
                        objectID=hit.get("objectID", ""),
                        title=hit.get("title", ""),
                        url=hit.get("url"),
                        author=hit.get("author", "unknown"),
                        points=hit.get("points", 0),
                        num_comments=hit.get("num_comments", 0),
                        created_at=datetime.fromisoformat(
                            hit.get("created_at", datetime.now().isoformat()).replace("Z", "+00:00")
                        ),
                        story_text=hit.get("story_text")
                    )
                    stories.append(story)

            # Sort by velocity score
            stories.sort(key=lambda s: s.velocity, reverse=True)
            stories = stories[:self.max_stories]

            # Extract trending keywords from titles
            keywords = self._extract_trending_keywords([s.title for s in stories])

            return HNTrendingResult(
                time_window=time_window,
                stories=stories,
                trending_keywords=keywords
            )

        except Exception as e:
            logger.error(f"Error getting trending stories: {e}")
            return HNTrendingResult(
                time_window=time_window,
                stories=[],
                trending_keywords=[]
            )

    async def get_user_analytics(
        self,
        username: str,
        include_submissions: bool = True
    ) -> Optional[HNUserAnalytics]:
        """Get user profile and analytics.

        Args:
            username: HN username
            include_submissions: Whether to fetch user's submissions

        Returns:
            HNUserAnalytics or None if user not found
        """
        try:
            # Get user profile
            response = await self.client.get(f"{self.BASE_URL}/users/{username}")
            response.raise_for_status()
            user_data = response.json()

            user = HNUser(
                username=user_data.get("username", username),
                created_at=datetime.fromtimestamp(user_data.get("created_at_i", 0)),
                karma=user_data.get("karma", 0),
                about=user_data.get("about"),
                submission_count=user_data.get("submission_count", 0),
                comment_count=user_data.get("comment_count", 0)
            )

            top_stories = []
            recent_activity = []

            if include_submissions:
                # Get user's stories
                params = {
                    "tags": f"author_{username},story",
                    "hitsPerPage": 20
                }

                response = await self.client.get(
                    f"{self.BASE_URL}/search",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", [])[:10]:
                    if hit.get("title"):
                        story = HNStory(
                            objectID=hit.get("objectID", ""),
                            title=hit.get("title", ""),
                            url=hit.get("url"),
                            author=username,
                            points=hit.get("points", 0),
                            num_comments=hit.get("num_comments", 0),
                            created_at=datetime.fromisoformat(
                                hit.get("created_at", datetime.now().isoformat()).replace("Z", "+00:00")
                            ),
                            story_text=hit.get("story_text")
                        )
                        top_stories.append(story)

                # Sort by points
                top_stories.sort(key=lambda s: s.points, reverse=True)

                # Get recent activity (stories + comments)
                params = {
                    "tags": f"author_{username}",
                    "hitsPerPage": 10
                }

                response = await self.client.get(
                    f"{self.BASE_URL}/search_by_date",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", []):
                    activity = {
                        "type": "story" if hit.get("title") else "comment",
                        "id": hit.get("objectID"),
                        "text": hit.get("title") or hit.get("comment_text", "")[:100],
                        "created_at": hit.get("created_at"),
                        "points": hit.get("points", 0)
                    }
                    recent_activity.append(activity)

            activity_summary = {
                "total_karma": user.karma,
                "total_submissions": user.submission_count or len(top_stories),
                "total_comments": user.comment_count or 0,
                "avg_story_score": sum(s.points for s in top_stories) / len(top_stories) if top_stories else 0,
                "account_age_days": (datetime.now() - user.created_at).days
            }

            return HNUserAnalytics(
                user=user,
                top_stories=top_stories[:5],
                recent_activity=recent_activity,
                activity_summary=activity_summary
            )

        except Exception as e:
            logger.error(f"Error getting user analytics for {username}: {e}")
            return None

    async def analyze_comments(
        self,
        story_id: str,
        max_comments: int = 50
    ) -> HNCommentAnalysis:
        """Analyze comments for a story.

        Args:
            story_id: Story ID to analyze
            max_comments: Maximum comments to analyze

        Returns:
            HNCommentAnalysis with comment insights
        """
        try:
            # Search for comments on this story
            params = {
                "tags": f"comment,story_{story_id}",
                "hitsPerPage": max_comments
            }

            response = await self.client.get(
                f"{self.BASE_URL}/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            comments = []
            commenters = set()
            sentiment_words = {
                "positive": ["great", "excellent", "love", "amazing", "awesome", "fantastic", "good"],
                "negative": ["bad", "terrible", "hate", "awful", "horrible", "poor", "wrong"],
                "neutral": ["okay", "fine", "average", "decent", "reasonable"]
            }

            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

            for hit in data.get("hits", []):
                if hit.get("comment_text"):
                    comment = HNComment(
                        objectID=hit.get("objectID", ""),
                        author=hit.get("author", "unknown"),
                        comment_text=hit.get("comment_text", ""),
                        created_at=datetime.fromisoformat(
                            hit.get("created_at", datetime.now().isoformat()).replace("Z", "+00:00")
                        ),
                        parent_id=str(hit.get("parent_id")) if hit.get("parent_id") else None,
                        story_id=story_id,
                        points=hit.get("points")
                    )
                    comments.append(comment)
                    commenters.add(comment.author)

                    # Simple sentiment analysis
                    text_lower = comment.comment_text.lower()
                    for sentiment, words in sentiment_words.items():
                        if any(word in text_lower for word in words):
                            sentiment_counts[sentiment] += 1
                            break
                    else:
                        sentiment_counts["neutral"] += 1

            # Extract discussion themes (simple keyword extraction)
            all_text = " ".join(c.comment_text for c in comments)
            themes = self._extract_trending_keywords([all_text], num_keywords=5)

            total_comments = len(comments)
            sentiment_summary = {
                "positive_ratio": sentiment_counts["positive"] / total_comments if total_comments > 0 else 0,
                "negative_ratio": sentiment_counts["negative"] / total_comments if total_comments > 0 else 0,
                "neutral_ratio": sentiment_counts["neutral"] / total_comments if total_comments > 0 else 0,
                "counts": sentiment_counts
            }

            return HNCommentAnalysis(
                story_id=story_id,
                total_comments=data.get("nbHits", 0),
                unique_commenters=len(commenters),
                top_comments=comments[:10],  # First 10 comments
                sentiment_summary=sentiment_summary,
                discussion_themes=themes
            )

        except Exception as e:
            logger.error(f"Error analyzing comments for story {story_id}: {e}")
            return HNCommentAnalysis(
                story_id=story_id,
                total_comments=0,
                unique_commenters=0,
                top_comments=[],
                sentiment_summary={},
                discussion_themes=[]
            )

    def _extract_trending_keywords(
        self,
        texts: List[str],
        num_keywords: int = 10
    ) -> List[str]:
        """Extract trending keywords from text list.

        Args:
            texts: List of text strings
            num_keywords: Number of keywords to extract

        Returns:
            List of trending keywords
        """
        # Simple keyword extraction based on word frequency
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "can", "could", "must", "shall",
            "i", "you", "he", "she", "it", "we", "they", "what", "which", "who",
            "when", "where", "why", "how", "this", "that", "these", "those",
            "hn", "hacker", "news", "show", "ask", "tell"
        }

        # Extract words from all texts
        words = []
        for text in texts:
            # Remove URLs and special characters
            text = re.sub(r'http\S+', '', text)
            text = re.sub(r'[^a-zA-Z\s]', ' ', text)

            # Split and filter
            for word in text.lower().split():
                if len(word) > 2 and word not in stop_words:
                    words.append(word)

        # Count frequency
        word_counts = Counter(words)

        # Get top keywords
        top_keywords = [word for word, _ in word_counts.most_common(num_keywords)]

        return top_keywords