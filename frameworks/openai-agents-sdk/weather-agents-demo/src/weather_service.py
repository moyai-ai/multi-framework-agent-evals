"""
Weather service integration for fetching weather data.

This module provides weather data retrieval using wttr.in API
and generates contextual weather recommendations.
"""

import httpx
from typing import Optional
from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    """Weather data response model."""

    city: str = Field(description="City name")
    temperature: str = Field(description="Temperature reading")
    conditions: str = Field(description="Weather conditions")
    recommendation: str = Field(description="Contextual recommendation")


def get_simulated_weather(city: str) -> Optional[WeatherResponse]:
    """
    Get simulated weather data for testing.

    Args:
        city: City name

    Returns:
        WeatherResponse with simulated data or None
    """
    # Simulated data for common cities
    simulated_data = {
        "San Francisco": {
            "temperature": "62°F (17°C)",
            "conditions": "Partly cloudy with fog in the morning",
        },
        "New York": {
            "temperature": "55°F (13°C)",
            "conditions": "Overcast with a chance of rain",
        },
        "Tokyo": {
            "temperature": "68°F (20°C)",
            "conditions": "Clear skies",
        },
        "London": {
            "temperature": "50°F (10°C)",
            "conditions": "Light rain",
        },
        "Paris": {
            "temperature": "59°F (15°C)",
            "conditions": "Cloudy",
        },
    }

    city_data = simulated_data.get(city)
    if city_data:
        recommendation = get_weather_recommendation(
            city_data["temperature"],
            city_data["conditions"]
        )
        return WeatherResponse(
            city=city,
            temperature=city_data["temperature"],
            conditions=city_data["conditions"],
            recommendation=recommendation
        )

    return None


async def get_weather_wttr(city: str) -> Optional[WeatherResponse]:
    """
    Fetch weather data from wttr.in API.

    Args:
        city: City name

    Returns:
        WeatherResponse with live data or None if fetch fails
    """
    try:
        url = f"https://wttr.in/{city}?format=%C+%t"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Parse response (format: "conditions temperature")
            data = response.text.strip()
            parts = data.rsplit(' ', 1)

            if len(parts) == 2:
                conditions = parts[0].strip()
                temperature = parts[1].strip()

                recommendation = get_weather_recommendation(temperature, conditions)

                return WeatherResponse(
                    city=city,
                    temperature=temperature,
                    conditions=conditions,
                    recommendation=recommendation
                )

    except Exception as e:
        # Log error but don't raise
        print(f"Error fetching weather from wttr.in: {e}")

    return None


def get_weather_recommendation(temperature: str, conditions: str) -> str:
    """
    Generate contextual weather recommendation.

    Args:
        temperature: Temperature string
        conditions: Weather conditions string

    Returns:
        Recommendation string
    """
    conditions_lower = conditions.lower()
    temp_lower = temperature.lower()

    recommendations = []

    # Temperature-based recommendations
    if "°f" in temp_lower:
        try:
            # Extract Fahrenheit temperature
            temp_f = int(''.join(filter(str.isdigit, temp_lower.split('°')[0])))
            if temp_f < 40:
                recommendations.append("It's quite cold - dress warmly with layers!")
            elif temp_f < 60:
                recommendations.append("It's cool - consider a light jacket.")
            elif temp_f > 80:
                recommendations.append("It's hot - stay hydrated and wear light clothing.")
        except:
            pass

    # Condition-based recommendations
    if any(word in conditions_lower for word in ["rain", "shower", "drizzle"]):
        recommendations.append("Bring an umbrella!")
    elif "snow" in conditions_lower:
        recommendations.append("Wear warm clothes and watch for slippery conditions.")
    elif "fog" in conditions_lower:
        recommendations.append("Drive carefully if you're heading out.")
    elif any(word in conditions_lower for word in ["clear", "sunny"]):
        recommendations.append("Great weather for outdoor activities!")
    elif "cloud" in conditions_lower:
        recommendations.append("Cloudy skies - a good day for indoor or outdoor plans.")

    if recommendations:
        return " ".join(recommendations)
    else:
        return "Have a great day!"


async def get_weather(city: str) -> WeatherResponse:
    """
    Get weather data for a city.

    Tries simulated data first, then falls back to live API.

    Args:
        city: City name

    Returns:
        WeatherResponse with weather data

    Raises:
        ValueError: If weather data cannot be retrieved
    """
    # Try simulated data first
    simulated = get_simulated_weather(city)
    if simulated:
        return simulated

    # Fall back to live API
    live_data = await get_weather_wttr(city)
    if live_data:
        return live_data

    # If all else fails, return a default response
    raise ValueError(f"Unable to retrieve weather data for {city}")
