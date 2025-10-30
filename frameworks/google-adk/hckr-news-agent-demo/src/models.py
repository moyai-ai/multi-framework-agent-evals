"""Pydantic models for Hacker News data structures."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HNStory(BaseModel):
    """Hacker News story model."""

    objectID: str = Field(..., description="Unique identifier for the story")
    title: str = Field(..., description="Story title")
    url: Optional[str] = Field(None, description="URL of the story")
    author: str = Field(..., description="Username of the author")
    points: int = Field(0, description="Story score/points")
    num_comments: int = Field(0, description="Number of comments")
    created_at: datetime = Field(..., description="Creation timestamp")
    story_text: Optional[str] = Field(None, description="Text content for self posts")

    @property
    def velocity(self) -> float:
        """Calculate velocity score (points per hour)."""
        from datetime import timezone
        # Make sure we're comparing timezone-aware datetimes
        now = datetime.now(timezone.utc)
        created = self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)
        hours_old = (now - created).total_seconds() / 3600
        # Add 2 to hours to prevent division issues and reduce recency bias
        return self.points / (hours_old + 2)


class HNComment(BaseModel):
    """Hacker News comment model."""

    objectID: str = Field(..., description="Unique identifier")
    author: str = Field(..., description="Comment author")
    comment_text: str = Field(..., description="Comment content")
    created_at: datetime = Field(..., description="Creation timestamp")
    parent_id: Optional[str] = Field(None, description="Parent item ID")
    story_id: Optional[str] = Field(None, description="Root story ID")
    points: Optional[int] = Field(None, description="Comment points if available")


class HNUser(BaseModel):
    """Hacker News user model."""

    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="Account creation date")
    karma: int = Field(0, description="User karma score")
    about: Optional[str] = Field(None, description="User bio/about text")
    submission_count: Optional[int] = Field(None, description="Number of submissions")
    comment_count: Optional[int] = Field(None, description="Number of comments")


class HNSearchResult(BaseModel):
    """Search result wrapper."""

    query: str = Field(..., description="Search query used")
    total_hits: int = Field(0, description="Total number of results")
    stories: List[HNStory] = Field(default_factory=list, description="List of stories")
    processing_time_ms: Optional[int] = Field(None, description="Query processing time")


class HNTrendingResult(BaseModel):
    """Trending stories result."""

    time_window: str = Field(..., description="Time window (24h, 7d, 30d)")
    stories: List[HNStory] = Field(default_factory=list, description="Trending stories")
    trending_keywords: List[str] = Field(default_factory=list, description="Extracted trending keywords")

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }


class HNUserAnalytics(BaseModel):
    """User analytics result."""

    user: HNUser = Field(..., description="User profile")
    top_stories: List[HNStory] = Field(default_factory=list, description="User's top stories")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent submissions and comments")
    activity_summary: Dict[str, int] = Field(default_factory=dict, description="Activity metrics")


class HNCommentAnalysis(BaseModel):
    """Comment thread analysis result."""

    story_id: str = Field(..., description="Story being analyzed")
    total_comments: int = Field(0, description="Total number of comments")
    unique_commenters: int = Field(0, description="Number of unique commenters")
    top_comments: List[HNComment] = Field(default_factory=list, description="Top-level comments")
    sentiment_summary: Dict[str, Any] = Field(default_factory=dict, description="Sentiment analysis")
    discussion_themes: List[str] = Field(default_factory=list, description="Main discussion themes")