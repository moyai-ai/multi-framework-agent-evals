# Hacker News Search Agent Demo

A Google ADK (Agent Development Kit) powered agent for searching and analyzing Hacker News content using the free Algolia HN Search API. This demo showcases structured JSON output for trending stories, user analytics, and comment sentiment analysis.

## Features

- **Search Stories**: Full-text search across Hacker News stories and comments
- **Trending Analysis**: Identify trending stories using velocity scoring (points/age)
- **User Analytics**: Analyze user profiles, karma, and submission history
- **Comment Analysis**: Extract sentiment and themes from discussion threads
- **Structured Output**: All responses in parseable JSON format
- **No Authentication Required**: Uses free public Algolia API

## Architecture

Built with:
- **Google ADK**: Agent framework with Gemini 2.0 Flash model
- **Algolia HN API**: Free, public Hacker News search API
- **Python 3.13**: With async/await for efficient API calls
- **Pydantic**: For structured data models
- **uv**: Modern Python package manager

## Prerequisites

- Python 3.13 or higher
- Google API key for Gemini access
- uv package manager ([install instructions](https://github.com/astral-sh/uv))

## Installation

1. Clone the repository:
```bash
cd hckr-news-agent-demo
```

2. Install dependencies with uv:
```bash
uv sync
```

## Usage

### Running Test Scenarios

Execute all test scenarios:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner
```

Run a specific scenario:
```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner src/scenarios/trending.json --verbose
```

### Available Scenarios

- `trending.json` - Test trending story analysis
- `search_keywords.json` - Test keyword search functionality
- `user_analysis.json` - Test user profile analysis
- `comment_sentiment.json` - Test comment sentiment analysis

### List Available Agents

```bash
unset VIRTUAL_ENV && uv run --env-file .env python -m src.runner --list-agents
```

Available agents:
- `hacker_news_agent` - Main agent with all capabilities
- `search_agent` - Specialized for story/comment search
- `trending_agent` - Analyzes trending stories
- `user_agent` - User profile analytics
- `comment_agent` - Comment thread analysis
- `multi_analysis_agent` - Sequential multi-step analysis

## API Examples

### Search Stories
```python
from src.tools import search_hacker_news

result = await search_hacker_news(
    query="artificial intelligence",
    search_type="story",
    num_results=30
)
```

### Get Trending Stories
```python
from src.tools import get_trending_stories

result = await get_trending_stories(
    time_window="24h",  # Options: "24h", "7d", "30d"
    min_score=50
)
```

### Analyze User
```python
from src.tools import analyze_user

result = await analyze_user(
    username="pg",
    include_submissions=True
)
```

### Analyze Comments
```python
from src.tools import analyze_story_comments

result = await analyze_story_comments(
    story_id="38823431",
    max_comments=50
)
```

## JSON Output Format

All agents return structured JSON responses:

### Trending Response
```json
{
  "query_type": "trending",
  "time_window": "24h",
  "results": [
    {
      "rank": 1,
      "title": "Story title",
      "url": "https://example.com",
      "author": "username",
      "points": 150,
      "comments": 45,
      "velocity_score": 12.5,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "trending_keywords": ["ai", "python", "startup"],
  "metadata": {
    "total_stories": 30,
    "min_score": 50,
    "generated_at": "2024-01-01T12:00:00"
  }
}
```

### Search Response
```json
{
  "query_type": "search",
  "search_query": "artificial intelligence",
  "results": [...],
  "metadata": {
    "total_hits": 150,
    "results_shown": 30,
    "search_time_ms": 45
  }
}
```

### User Analytics Response
```json
{
  "query_type": "user",
  "username": "pg",
  "profile": {
    "karma": 155736,
    "account_age_days": 4500,
    "about": "User bio...",
    "total_submissions": 150,
    "total_comments": 500
  },
  "top_stories": [...],
  "activity_summary": {...}
}
```

### Comment Analysis Response
```json
{
  "query_type": "comments",
  "story_id": "12345",
  "analysis": {
    "total_comments": 150,
    "unique_commenters": 75,
    "sentiment": {
      "positive_ratio": 0.4,
      "negative_ratio": 0.2,
      "neutral_ratio": 0.4
    },
    "top_themes": ["technology", "innovation"],
    "sample_comments": [...]
  }
}
```

## Testing

Run unit tests:
```bash
# Run all tests
unset VIRTUAL_ENV && uv run --env-file .env pytest

# Run without integration tests (no API calls)
unset VIRTUAL_ENV && uv run --env-file .env pytest -m "not integration"
```

## Project Structure

```
hckr-news-agent-demo/
  src/
    __init__.py
    agents.py           # Google ADK agent definitions
    prompts.py          # System prompts for agents
    tools.py            # HN API tool implementations
    hn_service.py       # Algolia API client service
    models.py           # Pydantic data models
    runner.py           # Scenario test runner
    scenarios/          # Test scenario JSON files
  tests/
    conftest.py         # Pytest fixtures
    test_agents.py      # Agent unit tests
    test_hn_service.py  # Service unit tests
  reports/              # Generated test reports
  pyproject.toml        # Project dependencies
  .env.example          # Environment template
  README.md             # This file
```

## Key Implementation Details

### Velocity Scoring Algorithm
Trending stories are ranked using velocity scoring:
```python
velocity = points / (hours_since_posted + 2)
```
The `+2` factor prevents division issues and reduces recency bias.

### Algolia API Endpoints
- Base URL: `https://hn.algolia.com/api/v1`
- No authentication required
- Endpoints used:
  - `/search` - Full-text search
  - `/search_by_date` - Date-sorted results
  - `/users/{username}` - User profiles
  - `/items/{id}` - Individual items

### Rate Limiting
The Algolia API has lenient rate limits (estimated 1 request/second). The service includes error handling and graceful degradation.

## Environment Variables

Configure in `.env`:
- `GOOGLE_API_KEY` - Your Google API key (required)
- `LOG_LEVEL` - Logging level (default: INFO)
- `VERBOSE` - Enable verbose output (default: false)
- `HN_MAX_STORIES` - Max stories to return (default: 30)
- `HN_SEARCH_LIMIT` - Max search results (default: 100)
- `HN_CACHE_TTL_MINUTES` - Cache duration (default: 15)

## Troubleshooting

### Missing API Key
```
Error: GOOGLE_API_KEY not found in environment
```
Solution: Add your Google API key to the `.env` file

### Import Errors
```
Error: No module named 'google.adk'
```
Solution: Run `uv sync` to install dependencies

### API Rate Limiting
If you encounter rate limiting, the service will gracefully return empty results. Wait a moment before retrying.

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass
2. Code follows existing patterns
3. JSON output maintains consistent structure
4. Documentation is updated

## License

This demo is for educational purposes. Please respect Hacker News and Algolia API usage guidelines.

## Acknowledgments

- Google ADK team for the agent framework
- Algolia for providing free Hacker News search API
- Hacker News community for the content