"""
Pytest configuration and fixtures for weather agent tests.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from src.context import WeatherAgentContext, create_initial_context, create_test_context
from src.weather_service import WeatherResponse


@pytest.fixture
def initial_context():
    """Fixture providing an initial weather agent context."""
    return create_initial_context()


@pytest.fixture
def test_context():
    """Fixture providing a test weather agent context with pre-set values."""
    return create_test_context(
        current_location="San Francisco",
        last_temperature="62°F (17°C)",
        last_conditions="Partly cloudy",
        last_recommendation="Great weather for outdoor activities!"
    )


@pytest.fixture
def mock_weather_response():
    """Fixture providing a mock weather response."""
    return WeatherResponse(
        city="San Francisco",
        temperature="62°F (17°C)",
        conditions="Partly cloudy with fog in the morning",
        recommendation="Great weather for outdoor activities! It's cool - consider a light jacket."
    )


@pytest.fixture
def mock_weather_service(monkeypatch, mock_weather_response):
    """Fixture that mocks the weather service to return predefined data."""
    async def mock_get_weather(city: str):
        if city == "San Francisco":
            return mock_weather_response
        elif city == "New York":
            return WeatherResponse(
                city="New York",
                temperature="55°F (13°C)",
                conditions="Overcast with a chance of rain",
                recommendation="Bring an umbrella! It's cool - consider a light jacket."
            )
        elif city == "Tokyo":
            return WeatherResponse(
                city="Tokyo",
                temperature="68°F (20°C)",
                conditions="Clear skies",
                recommendation="Great weather for outdoor activities!"
            )
        else:
            raise ValueError(f"Unable to retrieve weather data for {city}")

    from src import weather_service
    monkeypatch.setattr(weather_service, "get_weather", mock_get_weather)


@pytest.fixture
def scenario_files():
    """Fixture providing paths to test scenario files."""
    scenarios_dir = Path(__file__).parent.parent / "src" / "scenarios"
    return {
        "weather_queries": scenarios_dir / "weather_queries.json",
        "umbrella": scenarios_dir / "umbrella_recommendation.json",
        "multi_location": scenarios_dir / "multi_location.json",
    }


@pytest.fixture
def api_key():
    """Fixture to check if API key is available."""
    return os.environ.get("OPENAI_API_KEY")


@pytest.fixture
def skip_if_no_api_key(api_key):
    """Fixture to skip tests that require API key."""
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
